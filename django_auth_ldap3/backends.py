from django_auth_ldap3.conf import settings

from django.contrib.auth.models import User
from ldap3.core.exceptions import LDAPSocketOpenError
import hashlib
import ldap3
import logging

logger = logging.getLogger('django_auth_ldap3')

class LDAPUser(object):
    """
    A class representing an LDAP user returned from the directory.
    """

    connection = None
    _attrib_keys = [settings.UID_ATTRIB, 'cn', 'givenName', 'sn', 'mail']

    def __init__(self, connection, attributes):
        self.connection = connection
        for k, v in attributes.items():
            # Flatten any lists into their first element
            if type(v) == list and len(v) >= 1:
                v = v[0]
            setattr(self, k, v)

        # Set any missing attributes
        for k in self._attrib_keys:
            if not hasattr(self, k):
                setattr(self, k, None)

    def __str__(self):
        return getattr(self, settings.UID_ATTRIB)

class LDAPBackend(object):
    """
    An authentication backend for LDAP directories.
    """

    backend = None

    def __init__(self):
        self.backend = ldap3.Server(settings.URI)

    def __del__(self):
        # TODO: disconnect?
        pass

    def authenticate(self, username=None, password=None):
        """
        Required for Django auth. Authenticate the uesr against the LDAP
        backend and populate the local User model if this is the first
        time the user has authenticated.
        """

        # Authenticate against the LDAP backend and return an LDAPUser.
        ldap_user = self.retrieve_ldap_user(username, password)
        if ldap_user is None:
            logger.debug('Authentication failed for {}'.format(ldap_user))
            return None

        # If we get here, authentication is successful and we have an LDAPUser
        # instance populated with the user's attributes. We still need to check
        # group membership and populate a local User model.

        # Check LDAP group membership before creating a local user. The default
        # is '*' so any user can log in.
        if not self.check_group_membership(ldap_user, settings.LOGIN_GROUP):
            logger.debug('Failed group membership test: {} !memberOf {}'.format(ldap_user, settings.LOGIN_GROUP))
            return None

        # Check if this user is part of the admin group.
        admin = False
        if settings.ADMIN_GROUP:
            admin = self.check_group_membership(ldap_user, settings.ADMIN_GROUP)

        # Get or create the User object in Django's auth, populating it with
        # fields from the LDAPUser. Note we set the password to a random hash
        # as authentication should never occur directly off this user.
        user, created = User.objects.get_or_create(username=username, defaults={
                'password': hashlib.sha1().hexdigest(),
                'first_name': ldap_user.givenName,
                'last_name': ldap_user.sn,
                'email': ldap_user.mail,
                'is_superuser': False,
                'is_staff': admin,
                'is_active': True
        })

        # If the user wasn't created, update its fields from the directory.
        if not created:
            user.first_name = ldap_user.givenName
            user.last_name = ldap_user.sn
            user.email = ldap_user.mail
            user.is_staff = admin
            user.save()

        return user

    def get_user(self, user_id):
        """
        Required for Django auth.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def check_group_membership(self, ldap_user, group_dn):
        """
        Check the LDAP user to see if it is a member of the given group.
        
        This is straightforward with OpenLDAP but tricky with AD as due to
        the weird way AD handles "primary" group membership, we must test for
        a separate attribute as well as the usual 'memberof' as the primary
        group is not returned with that filter.
        """

        # Don't bother search directory if '*' was given: this denotes any group
        # so pass the test immediately.
        if group_dn == '*':
            return True

        # Hack for AD: fetch the group's attributes and check for the
        # primaryGroupToken. This will return 0 results in OpenLDAP and hence
        # be ignored.
        pgt = None
        group_attribs = self.search_ldap(ldap_user.connection, '(distinguishedName={})' \
                .format(group_dn), attributes=['primaryGroupToken'])
        if group_attribs:
            pgt = group_attribs.get('primaryGroupToken', None)
            if type(pgt) == list:
                pgt = pgt[0]

        # Now perform our group membership test. If the primary group token is not-None,
        # then we wrap the filter in an OR and test for that too.
        search_filter = '(&(objectClass=user)({}={})(memberof={}))'.format(
                settings.UID_ATTRIB, str(ldap_user), group_dn)
        if pgt:
            search_filter = '(|{}(&(cn={})(primaryGroupID={})))'.format(search_filter, ldap_user.cn, pgt)
        
        # Return True if user is a member of group
        r = self.search_ldap(ldap_user.connection, search_filter)
        return r is not None

    def retrieve_ldap_user(self, username, password):
        """
        Proxy method for retrieving an LDAP user depending on configuration.
        Currently we only support direct binding.
        """
        return self.bind_ldap_user(username, password)

    def search_ldap(self, connection, ldap_filter, **kwargs):
        """
        Searches the LDAP directory against the given LDAP filter in the form
        of '(attr=val)' e.g. '(uid=test)'.

        Any keyword arguments will be passed directly to the underlying search
        method.

        A dictionary of attributes will be returned.
        """
        connection.search(settings.BASE_DN, ldap_filter, **kwargs)
        entry = None
        for d in connection.response:
            if d['type'] == 'searchResEntry':
                entry = d['attributes']
                entry['dn'] = d['dn']
                break
        return entry

    def bind_ldap_user(self, username, password):
        """
        Attempts to bind the specified username and password and returns
        an LDAPUser object representing the user.

        Returns None if the bind was unsuccessful.

        This implements direct binding.
        """

        # Construct the user to bind as
        if settings.BIND_TEMPLATE:
            # Full CN
            ldap_bind_user = settings.BIND_TEMPLATE.format(username=username,
                    base_dn=settings.BASE_DN)
        elif settings.USERNAME_PREFIX:
            # Prepend a prefix: useful for DOMAIN\user
            ldap_bind_user = settings.USERNAME_PREFIX + username
        elif settings.USERNAME_SUFFIX:
            # Append a suffix: useful for user@domain
            ldap_bind_user = username + settings.USERNAME_SUFFIX
        logger.debug('Attempting to authenticate to LDAP by binding as ' + ldap_bind_user)

        try:
            c = ldap3.Connection(self.backend,
                    read_only=True,
                    lazy=False,
                    auto_bind=True,
                    client_strategy=ldap3.SYNC,
                    authentication=ldap3.SIMPLE,
                    user=ldap_bind_user,
                    password=password)
        except ldap3.core.exceptions.LDAPSocketOpenError as e:
            logger.error('LDAP connection error: ' + str(e))
            return None
        except ldap3.core.exceptions.LDAPBindError as e:
            if 'invalidCredentials' in str(e):
                # Invalid bind DN or password
                return None
            else:
                logger.error('LDAP bind error: ' + str(e))
                return None
        except Exception as e:
            logger.exception('Caught exception when trying to connect and bind to LDAP')
            raise

        # Search for the user using their full DN
        search_filter = '({}={})'.format(settings.UID_ATTRIB, username)
        attributes = self.search_ldap(c, search_filter, attributes=LDAPUser._attrib_keys, size_limit=1)
        if not attributes:
            logger.error('LDAP search error: no results for ' + search_filter)
            return None

        # Construct an LDAPUser instance for this user
        return LDAPUser(c, attributes)
