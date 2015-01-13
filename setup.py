from setuptools import find_packages, setup

setup(
    name='django_auth_ldap3',
    version='0.9.0',
    license='BSD',
    author='Sam Kingston',
    author_email='sam@sjkwi.com.au',
    description='A library for connecting Django\'s authentication system to an LDAP directory',
    url='https://github.com/sjkingo/django_auth_ldap3',
    install_requires=[
        'Django >= 1.7',
        'ldap3 >= 0.9.7.1',
    ],
    packages=find_packages(),
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP',
    ],
)
