import logging
import ssl

import ldap3
from ldap3 import Server, Connection, SYNC
from ldap3.core.exceptions import LDAPException
from ldap3.core.tls import Tls
from ldap3.utils.uri import parse_uri
from ldap3.utils.conv import escape_filter_chars

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

# Default-Settings
DEFAULT_LDAP_SYNC_USER_ATTRIBUTES = {
    'username': 'sAMAccountName',
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}
DEFAULT_LDAP_TIMEOUT = 5

class Ldap(object):
    def __init__(self):
        ''' Modul initialisieren'''

        # Logger
        self.logger = logging.getLogger(__name__)

        # Get Settings
        self.LDAP_SYNC_URI = settings.LDAP_SYNC_CONNECTION['uri']
        self.LDAP_PARAMS = parse_uri(self.LDAP_SYNC_URI)
        self.LDAP_SYNC_BASE_USER = settings.LDAP_SYNC_CONNECTION['username']
        self.LDAP_SYNC_BASE_PASS = settings.LDAP_SYNC_CONNECTION['password']
        self.LDAP_TIMEOUT = getattr(settings.LDAP_SYNC_CONNECTION, 'timeout', DEFAULT_LDAP_TIMEOUT)
        self.LDAP_SYNC_USER_ATTRIBUTES = getattr(settings, 'LDAP_SYNC_USER_ATTRIBUTES', DEFAULT_LDAP_SYNC_USER_ATTRIBUTES)

        # Check MaxLength
        User = get_user_model()
        self.USER_MODEL_ATTRS_MAX_LENGTH = {}
        for field_name in self.LDAP_SYNC_USER_ATTRIBUTES.keys():
            field = User._meta.get_field(field_name)
            self.USER_MODEL_ATTRS_MAX_LENGTH[field_name] = field.max_length

    @cached_property
    def connection(self):
        ''' Connecion '''

        # Verbindungsparameter für den LDAP-Server
        server_options = {
            'host': self.LDAP_PARAMS['host'],
            'use_ssl': False,
            'port': self.LDAP_PARAMS['port'],
            'connect_timeout': self.LDAP_TIMEOUT,
        }
        if self.LDAP_PARAMS['ssl']:
            server_options['use_ssl'] = True
            server_options['tls'] = Tls(validate=ssl.CERT_REQUIRED)

        # Authentifizierung am Server
        ldap_server = Server(**server_options)
        connection_options = {
            'server': ldap_server,
            'auto_bind': True,
            'user': self.LDAP_SYNC_BASE_USER,
            'password': self.LDAP_SYNC_BASE_PASS,
            'client_strategy': SYNC,
        }
        try:
            return Connection(**connection_options)
        except LDAPException:
            self.logger.warning("LDAP connection failed, LDAP updates will not be available.")
            return None

    def get_username_key(self):
        ''' Return LDAP-Key which represents Django-Username '''

        return self.LDAP_SYNC_USER_ATTRIBUTES['username']

    def get_django_attributes_for_user(self, username):
        ''' Return Django-Attributes for User '''

        # Get from LDAP
        ldap_attributes = list(self.LDAP_SYNC_USER_ATTRIBUTES.values())
        ldap_user = self.get_user(username, attributes=ldap_attributes)

        # Return for Django (use Mapping)
        model_attrs = {}
        for django_key, ldap_key in self.LDAP_SYNC_USER_ATTRIBUTES.items():
            if ldap_key in ldap_user and ldap_user[ldap_key]:
                # Limit the LDAP value to the `max_length` of the field. Otherwise
                # we run into validation errors.
                model_attrs[django_key] = ldap_user[ldap_key][0:self.USER_MODEL_ATTRS_MAX_LENGTH[django_key]]
        return model_attrs

    def get_user(self, username, attributes=ldap3.ALL_ATTRIBUTES):
        ''' Returns the specified user from LDAP, without doing any conversion. '''

        cleaned_username = escape_filter_chars(username).split('@')[0]
        search_kwargs = {
            'search_base': self.LDAP_PARAMS['base'],
            'search_filter': '(sAMAccountName=%s)' %cleaned_username,
            'attributes': attributes,
        }

        conn = self.connection
        if not conn:
            return {}
        try:
            self.logger.debug("Suche Nutzer: " + username)
            result = conn.search(**search_kwargs)
        except LDAPException:
            # Try one more time before raising the exception
            # @TODO: Catch exception in User.pre_save()
            try:
                conn.unbind()
            except:
                pass
            conn.bind()
            result = conn.search(**search_kwargs)

        if not result or not conn.response[0] or 'attributes' not in conn.response[0]:
            return {}
        else:
            return conn.response[0]['attributes']

    def get_dn(self, common_name: str):
        ''' Returns DistinguishedName from CommonName '''

        # Search for CN
        self.connection.search(
            search_base=self.LDAP_PARAMS['base'],
            search_scope=ldap3.SUBTREE,
            search_filter=f"(cn={common_name})",
            attributes=['DistinguishedName']
        )

        # Return
        if len(self.connection.response) == 0:
            return None
        return self.connection.response[0]['attributes']['DistinguishedName']

    def get_group_members(self, group_dn: str):
        ''' Returns all Members from a specific group '''

        # Search for Group-Members
        attributes = list(self.LDAP_SYNC_USER_ATTRIBUTES.values())
        search_filter = f"(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:={group_dn}))"
        entry_generator = self.connection.extend.standard.paged_search(
            search_base=self.LDAP_PARAMS['base'],
            search_scope=ldap3.SUBTREE,
            search_filter=search_filter,
            attributes=attributes,
            paged_size=500,
            generator=True,
            get_operational_attributes=False,
        )

        # Ergebnisse parsen
        member_list = []
        for entry in entry_generator:
            if entry['type'] == 'searchResEntry':
              member_list.append(entry['attributes'])
        return member_list
