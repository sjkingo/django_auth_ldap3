# django_auth_ldap3

`django_auth_ldap3` is a library for connecting Django's authentication system
to an LDAP directory.  Unlike other similar libraries, it uses the excellent
`ldap3` pure-Python library.  It has a sane default configuration that requires
minimal customisation and has been tested against OpenLDAP and Active
Directory.

It supports Django 1.7+ and Python 3.3+.

### Installation

The easiest way is to install from PyPi using pip:

```
$ pip install django_auth_ldap3
```

Alternatively you may install from the latest commit on the `master` branch:

```
$ pip install -e git+https://github.com/sjkingo/django_auth_ldap3.git#egg=django_auth_ldap3
```

### Base configuration

1. First, add the LDAP backend to Django's `AUTHENTICATION_BACKENDS` tuple:

   ```
   AUTHENTICATION_BACKENDS = (
       'django_auth_ldap3.backends.LDAPBackend',
       'django.contrib.auth.backends.ModelBackend',
   )
   ```

   We specify `ModelBackend` as a fallback in case any superusers are defined locally in the database.

2. `django_auth_ldap3` requires at a minimum 2 settings to specify the connection to the directory server:

   ```
   AUTH_LDAP_URI = 'ldap://localhost:389'
   AUTH_LDAP_BASE_DN = 'dc=example,dc=com'
   ```

   Any valid LDAP URI is allowed for the `AUTH_LDAP_URI` setting, with the port
   being optional and will default to 389 if not specified. `AUTH_LDAP_BASE_DN`
   must be set to the base container to perform any subtree searches from.

### Configuration for authenticating

There are two methods of authenticating against an LDAP directory:

#### Method 1: Direct binding

This is by far the easiest method to use, and requires minimal configuration.
In this method, the username and password provided during authentication are
used to bind directly to the directory. If the bind fails, the
username/password combination (or bind DN template [1]) is incorrect.

This authentication method is best suited toward an OpenLDAP directory.

[1] When direct binding, there is no way to distinguish between an incorrect
username/password and the bind template being incorrect, since both result in
an invalid bind.

Only 1 extra setting is required for direct binding to an OpenLDAP directory:

* `AUTH_LDAP_BIND_TEMPLATE`: the template to use when constructing the user to bind. For example: `uid={username},ou=People`. It must contain `{username}` somewhere which will be substituted for the username that is being authenticated.

Alternatively you may wish to change the attribute that matches the Django username - by defualt it is `uid`:

* `AUTH_LDAP_UID_ATTRIB`: the attribute used for a unique username (e.g. `uid` or `sAMAccountName`)

The key requirement for direct binding is that a unique common name must be able
to be constructed from a given username, for instance:

```
'jsmith' -> 'uid=jsmith,ou=People,dc=example,dc=com'
```

A point to note here is that if you are using Active Directory, you may bind
with a full user principal instead, such as `DOMAIN\user` or `user@domain`.
This can be accomplished by setting one of the following settings:

* `AUTH_LDAP_USERNAME_PREFIX`: e.g. `DOMAIN\`
* `AUTH_LDAP_USERNAME_SUFFIX`: e.g. `@domain.com`

If using either of these settings, set `AUTH_LDAP_BIND_TEMPLATE` to `None`. You
will almost certainly want to change the `AUTH_LDAP_UID_ATTRIB` to
`sAMAccountName`.

#### Method 2: Search and bind

The second method is more flexible but requires more directory-specific
configuration: it allows you to filter users by any valid LDAP filter, across a
directory tree.

It is yet to be implemented in this library.

### Example configuration for OpenLDAP

```
AUTH_LDAP_URI = 'ldap://localhost:389'
AUTH_LDAP_BASE_DN = 'ou=People,dc=example,dc=com'
AUTH_LDAP_BIND_TEMPLATE = 'uid={username},ou=People,dc=example,dc=com'
```

### Example configuration for Active Directory

```
AUTH_LDAP_URI = 'ldap://DC1.example.com:389'
AUTH_LDAP_BASE_DN = 'dc=example,dc=com'
AUTH_LDAP_BIND_TEMPLATE = None
AUTH_LDAP_USERNAME_PREFIX = 'DOMAIN\\'
AUTH_LDAP_UID_ATTRIB = 'sAMAccountName'
```

