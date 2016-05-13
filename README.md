# django_auth_ldap3

This is a small library for connecting Django's authentication system to an
LDAP directory.  Unlike other similar libraries, it and its dependencies are
pure-Python and do not require any special system headers to run, making it
perfect for running in a hosted virtualenv.

It has a sane default configuration that requires minimal customization, and
has been tested against OpenLDAP and Microsoft's Active Directory.

It is licensed under the [BSD license](https://github.com/sjkingo/django_auth_ldap3/blob/master/LICENSE).

It is known to work with:

* Python 2.7, 3.3-3.5
* Django 1.6.10, 1.7-1.9

Note at some point in the future, support for Python 2.7/3.3 and Django 1.6/1.7 will be dropped (see [issue #15](https://github.com/sjkingo/django_auth_ldap3/issues/15)).

[![Latest Version](http://img.shields.io/pypi/v/django_auth_ldap3.svg)](https://pypi.python.org/pypi/django_auth_ldap3/)
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://github.com/sjkingo/django_auth_ldap3/blob/master/LICENSE)

## Installation

The easiest way is to install from [PyPi](https://pypi.python.org/pypi/django_auth_ldap3) using pip:

```
$ pip install django_auth_ldap3
```

Alternatively you may install from the latest commit on the `master` branch:

```
$ pip install -e git+https://github.com/sjkingo/django_auth_ldap3.git#egg=django_auth_ldap3
```

## Base configuration

A full configuration reference of all settings [is available](https://github.com/sjkingo/django_auth_ldap3#configuration-reference).

1. First, add the LDAP backend to Django's `AUTHENTICATION_BACKENDS` tuple in `settings.py`:

   ```
   AUTHENTICATION_BACKENDS = (
       'django_auth_ldap3.backends.LDAPBackend',
       'django.contrib.auth.backends.ModelBackend',
   )
   ```

   We specify `ModelBackend` here as a fallback in case any superusers are defined locally in the database.

2. Point the configuration to the directory server with only two required settings:

   ```
   AUTH_LDAP_URI = 'ldap://localhost:389'
   AUTH_LDAP_BASE_DN = 'dc=example,dc=com'
   ```

   * Any valid [LDAP
   URI](https://www.centos.org/docs/5/html/CDS/ag/8.0/LDAP_URLs-Examples_of_LDAP_URLs.html)
   is allowed for the `AUTH_LDAP_URI` setting (the port is optional and will
   default to 389 if not specified).

   * TLS has been supported since [v0.9.5](https://github.com/sjkingo/django_auth_ldap3/releases/tag/v0.9.5) with `AUTH_LDAP_TLS`.

   * `AUTH_LDAP_BASE_DN` must be set to the base container to perform any subtree
   searches from.

## Configuration for authenticating

There are two methods of authenticating against an LDAP directory.

### Method 1: Direct binding

This is by far the easiest method to use, and requires minimal configuration.
In this method, the username and password provided during authentication are
used to bind directly to the directory. If the bind fails, the
username/password combination (or `AUTH_LDAP_BIND_TEMPLATE` [1]) is incorrect.

[1] When direct binding, there is no way to distinguish between an incorrect
username/password and the bind template being incorrect, since both result in
an invalid bind.

Only one extra setting is required for direct binding to an OpenLDAP directory:

* `AUTH_LDAP_BIND_TEMPLATE`: the template to use when constructing the user to bind. For example: `uid={username},ou=People`. It must contain `{username}` somewhere which will be substituted for the username that is being authenticated.

Alternatively you may wish to change the attribute that matches the Django username - by default it is `uid`:

* `AUTH_LDAP_UID_ATTRIB`: the attribute used for a unique username (e.g. `uid` or `sAMAccountName`)

The key requirement for direct binding is that a distinguished name is able to
be constructed from a given username, for instance:

* username `'jsmith'` is known with a distinguished name of `'uid=jsmith,ou=People,dc=example,dc=com'` in the directory

A point to note here is that if you are using Active Directory, you may tell
the backend to bind with a full user principal instead, such as `DOMAIN\user`
or `user@domain`.  This can be accomplished by setting one of the following
settings:

* `AUTH_LDAP_USERNAME_PREFIX`: e.g. `DOMAIN\`
* `AUTH_LDAP_USERNAME_SUFFIX`: e.g. `@domain.com`

If using either of these settings, set `AUTH_LDAP_BIND_TEMPLATE` to `None`. You
will almost certainly want to change the `AUTH_LDAP_UID_ATTRIB` to
`sAMAccountName`.

### Method 2: Search and bind

The second method is more flexible but requires more directory-specific
configuration: it allows you to filter users by any valid LDAP filter, across a
directory tree.

It is yet to be implemented in this library. See [issue #2](https://github.com/sjkingo/django_auth_ldap3/issues/2).

## Group membership

Sometimes it is desirable to restrict authentication to users that are members
of a specific LDAP group. This may be accomplished by setting the
`AUTH_LDAP_LOGIN_GROUP` setting. By default it is set to `'*'`; any valid user
may authenticate. If you wish to restrict this, change the setting to the
distinguished name of a group, for example:

```
AUTH_LDAP_LOGIN_GROUP = 'cn=Web Users,ou=Groups,dc=example,dc=com'
```

You may also allow a subset of users to authenticate to the Django admin
interface by setting the `AUTH_LDAP_ADMIN_GROUP` setting. By default this is
set to `None`, indicating no user may have access to the admin. If you wish to
allow access, change the setting to the distinguished name of a group, for
example:

```
AUTH_LDAP_ADMIN_GROUP = 'cn=Admin Users,ou=Groups,dc=example,dc=com'
```

Should you wish to map LDAP groups to Django groups, you can use the `AUTH_LDAP_GROUP_MAP`
setting.  By default it is set to `None`, indicating that no mapping will occur.  The mapping is
done in the form of a dict where the keys are LDAP group DNs and the values are sequences of Django groups,
for example:

```
AUTH_LDAP_GROUP_MAP = {
    'cn=Admin Users,ou=Groups,dc=example,dc=com': ('site_admins', 'editors'),
    'cn=Authors,ou=Groups,dc=example,dc=com': ('editors',)
}
```

Note that any Django groups you list will be controlled by this mapping, and can't be manually managed,
because users will be added or removed from the groups according to their LDAP group memberships at login.
Any Django groups not included in the mappings will be unaffected.

## Example configuration for OpenLDAP

```
AUTH_LDAP_URI = 'ldap://localhost:389'
AUTH_LDAP_BASE_DN = 'ou=People,dc=example,dc=com'
AUTH_LDAP_BIND_TEMPLATE = 'uid={username},{base_dn}'
```

The last line is only required if the bind template differs from the default.

## Example configuration for Active Directory

```
AUTH_LDAP_URI = 'ldap://DC1.example.com:389'
AUTH_LDAP_BASE_DN = 'dc=example,dc=com'
AUTH_LDAP_BIND_TEMPLATE = None
AUTH_LDAP_USERNAME_PREFIX = 'DOMAIN\\'
AUTH_LDAP_UID_ATTRIB = 'sAMAccountName'
```

## Configuration reference

#### `AUTH_LDAP_BASE_DN`

Default: `'dc=example,dc=com'`

**Required.** The base container to perform any subtree searches from.

#### `AUTH_LDAP_BIND_TEMPLATE`

Default: `'uid={username},{base_dn}'`

**Required.** Template used to construct the distinguished name of the user to authenticate.

Valid substitution specifiers are:

* `{username}` (required): the username being authenticated
* `{base_dn}`: will be substituted for `AUTH_LDAP_BASE_DN`

#### `AUTH_LDAP_URI`

Default: `'ldap://localhost'`

**Required.** A valid LDAP URI that specifies a connection to a directory server.

TLS has been supported since [v0.9.5](https://github.com/sjkingo/django_auth_ldap3/releases/tag/v0.9.5) with `AUTH_LDAP_TLS`.

#### `AUTH_LDAP_ADMIN_GROUP`

Default: `None`

*Optional.* Distinguished name of the group of users allowed to access the admin area, or `None`
to deny all.

#### `AUTH_LDAP_GROUP_MAP`

Default: `None`

*Optional.* Dictionary of LDAP groups to Django groups to perform mapping on.
See *Group membership*, above, for more details.

*Added in version 0.9.4*

#### `AUTH_LDAP_LOGIN_GROUP`

Default: `'*'`

*Optional.* Restrict authentication to users that are a member of this group
(distinguished name). `'*'` indicates any user may authenticate.

#### `AUTH_LDAP_UID_ATTRIB`

Default: `'uid'`

*Optional.* The unique attribute in the directory that stores the username. For
Active Directory this will be `sAMAccountName`.

#### `AUTH_LDAP_USERNAME_PREFIX`

Default: `None`

*Optional.* String to prefix the username before binding. This is used for `DOMAIN\user` principals.

You must set `AUTH_LDAP_BIND_TEMPLATE` to `None` when using this option.

#### `AUTH_LDAP_USERNAME_SUFFIX`

Default: `None`

*Optional.* String to suffix the username before binding. This is used for `user@domain` principals.

You must set `AUTH_LDAP_BIND_TEMPLATE` to `None` when using this option.

*Added in version 0.9.5*

#### `AUTH_LDAP_TLS`

*Optional.* Flag to enable LDAP over TLS. Further options can be configured through `AUTH_LDAP_TLS_CA_CERTS`,
`AUTH_LDAP_TLS_VALIDATE`, `AUTH_LDAP_TLS_PRIVATE_KEY`, and `AUTH_LDAP_TLS_LOCAL_CERT`.

Default: `False`

#### `AUTH_LDAP_TLS_CA_CERTS`
*Optional.* String to the location of the file containing the certificates of the certification authorities.

It's checked only if `AUTH_LDAP_TLS_VALIDATE` is set to `True`.

Default: It will use the system wide certificate store.

#### `AUTH_LDAP_TLS_VALIDATE`
*Optional.* Specifies if the server certificate must be validated.

Default: `True`

#### `AUTH_LDAP_TLS_PRIVATE_KEY`
*Optional.* Specifies the location for the file with the private key of the client.

#### `AUTH_LDAP_TLS_LOCAL_CERT`
*Optional.* Specifies the location for the file with the certificate of the server.

## Caveats

When using this library, it is strongly recommended to not manually
modify the usernames in the Django user table (either through the admin or modifying a 
`User.username` field). See issues [#7](https://github.com/sjkingo/django_auth_ldap3/issues/7) and [#9](https://github.com/sjkingo/django_auth_ldap3/issues/9) for more details.
