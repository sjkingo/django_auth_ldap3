Changelog
=========

### 0.9.6 - 2016-05-05

* Python 3.5 and Django 1.9 officially supported (@sjkingo)
* #19: Pass missing LDAP fields to Django as blank strings to prevent exception when creating
  a new user (@alandmore)

### 0.9.5 - 2016-03-30

* #3: New feature `AUTH_LDAP_TLS` allows LDAP connections to be established over TLS (@_wayo)

### 0.9.4 - 2016-01-21

* Use proxy method for getting `User` instance to support Django's custom user models (@alandmoore)
* New feature `AUTH_LDAP_GROUP_MAP` to map LDAP groups to Django for authorization (@alandmore)

### 0.9.3 - 2015-07-06

* Fix bug with case-insensitive LDAP usernames creating duplicate users in
  Django's auth database (@rmassoth, @sjkingo) - [issue #7](https://github.com/sjkingo/django_auth_ldap3/issues/7)

### 0.9.2 - 2015-04-27

* Fix bug where primary group membership in AD would succeed regardless
  of actual membership (@gianlo) - PR #5

### 0.9.1 - 2015-01-14

* Updated dependencies to allow Python 2.7 and Django 1.6.10
* Tweaked package classifiers

### 0.9.0 - 2015-01-14

* Initial working version
