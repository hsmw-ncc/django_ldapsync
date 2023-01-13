from setuptools import setup, find_packages

setup(name='ldapsync',
    version='1.2',
    description='Synchronisiert Django-Nutzer mit dem LDAP',
    author='Tom Schreiber',
    author_email='tom.schreiber@hs-mittweida.de',
    url='https://github.com/HSMW-NCC/django_ldapsync',
    packages=find_packages(exclude=['test']),
    install_requires=[
        'django>=3',
        'ldap3>=2.2.0',
    ],
)
