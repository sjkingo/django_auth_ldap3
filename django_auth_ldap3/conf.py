from django.conf import settings as django_settings

class LDAPSettings(object):
    """
    Class that provides access to the LDAP settings specified in Django's
    settings, with defaults set if they are missing.

    Settings are prefixed in Django's settings, but are used here without prefix.
    So `AUTH_LDAP_URI` becomes `settings.URI`.
    """

    prefix = 'AUTH_LDAP_'
    defaults = {
        'ADMIN_GROUP': None,
        'BASE_DN': 'dc=example,dc=com',
        'BIND_TEMPLATE': 'uid={username},{base_dn}',
        'GROUP_MAP': None,
        'LOGIN_GROUP': '*',
        'UID_ATTRIB': 'uid',
        'USERNAME_PREFIX': None,
        'USERNAME_SUFFIX': None,
        'URI': 'ldap://localhost',
        'TLS': False,
        'TLS_CA_CERTS': None,
        'TLS_VALIDATE': True,
        'TLS_PRIVATE_KEY': None,
        'TLS_LOCAL_CERT': None,
    }

    def __init__(self):
        for name, default in self.defaults.items():
            v = getattr(django_settings, self.prefix + name, default)
            setattr(self, name, v)

    @property
    def settings_dict(self):
        return {k: getattr(self, k) for k in self.defaults.keys()}

settings = LDAPSettings()
