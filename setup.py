from setuptools import setup, find_packages

setup(name='django_ldapsync',
    version='2.0.2',
    description='Synchronisiert Django-Nutzer mit dem LDAP',
    author='Tom Schreiber',
    author_email='tom.schreiber@hs-mittweida.de',
    url='https://github.com/HSMW-NCC/django_ldapsync',
    packages=find_packages(exclude=['test']),
    install_requires=[
        'django>=4',
        'ldap3>=2.9.0',
    ],
)
