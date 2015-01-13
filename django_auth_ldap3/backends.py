from django_auth_ldap3.conf import settings
from django_auth_ldap3.exceptions import *

import ldap3
from ldap3.core.exceptions import LDAPSocketOpenError
import logging

logger = logging.getLogger('django_auth_ldap3')

class LDAPUser(object):
    """
    A class representing an LDAP user returned from the directory.
    """

    _attrib_keys = [settings.UID_ATTRIB, 'cn', 'givenName', 'sn', 'mail']

    def __init__(self, attributes):
        for k, v in attributes.items():
            # Flatten any lists into their first element
            if type(v) == list and len(v) >= 1:
                v = v[0]
            setattr(self, k, v)

        # Set any missing attributes
        for k in self._attrib_keys:
            if not hasattr(self, k):
                setattr(self, k, None)

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
        Required for Django auth.
        """
        ldap_user = self.retrieve_ldap_user(username, password)
        if ldap_user is None:
            return None

        # TODO: get_or_create() against django.models.User

    def get_user(self, user_id):
        """
        Required for Django auth.
        """
        # TODO: get LDAP user with model?
        pass

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
            ldap_bind_user = settings.BIND_TEMPLATE.format(username=username)
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
        return LDAPUser(attributes)
