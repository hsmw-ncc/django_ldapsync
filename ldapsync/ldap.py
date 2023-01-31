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
    'givenName': 'first_name',
    'sn': 'last_name',
    'mail': 'email',
}
DEFAULT_LDAP_SEARCH_ATTRIBUTES = {
  'eduPersonPrincipalName',
  'sn',
  'givenName',
  'mail'
}
DEFAULT_LDAP_TIMEOUT = 5

class Ldap(object):
    def __init__(self):
        ''' Modul initialisieren'''

        # Logger
        self.logger = logging.getLogger(__name__)

        # Get Settings
        self.LDAP_SYNC_URI = settings.LDAP['uri']
        self.LDAP_PARAMS = parse_uri(self.LDAP_SYNC_URI)
        self.LDAP_SYNC_BASE_USER = settings.LDAP['username']
        self.LDAP_SYNC_BASE_PASS = settings.LDAP['password']
        self.LDAP_SYNC_USER_ATTRIBUTES = getattr(settings.LDAP, 'sync_user_attributes', DEFAULT_LDAP_SYNC_USER_ATTRIBUTES)
        self.LDAP_SEARCH_ATTRIBUTES = getattr(settings.LDAP, 'search_attributes', DEFAULT_LDAP_SEARCH_ATTRIBUTES)
        self.LDAP_TIMEOUT = getattr(settings.LDAP, 'timeout', DEFAULT_LDAP_TIMEOUT)

        # Check MaxLength
        User = get_user_model()
        self.USER_MODEL_ATTRS_MAX_LENGTH = {}
        for field_name in self.LDAP_SYNC_USER_ATTRIBUTES.values():
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

    def get_attributes(self, username):
        ''' This method is not part of the public API. Do not use it. '''

        model_attrs = {}
        ldap_user = self.get_user(username, self.LDAP_SYNC_USER_ATTRIBUTES.keys())

        for attr in self.LDAP_SYNC_USER_ATTRIBUTES:
            if attr in ldap_user and ldap_user[attr]:
                field_name = self.LDAP_SYNC_USER_ATTRIBUTES[attr]
                ldap_value = ldap_user[attr]
                # Limit the LDAP value to the `max_length` of the field. Otherwise
                # we run into validation errors.
                model_attrs[field_name] = ldap_value[0:self.USER_MODEL_ATTRS_MAX_LENGTH[field_name]]
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

        if not result:
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
        search_filter = f"(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:={group_dn}))"
        entry_generator = self.connection.extend.standard.paged_search(
            search_base=self.LDAP_PARAMS['base'],
            search_scope=ldap3.SUBTREE,
            search_filter=search_filter,
            attributes=self.LDAP_SEARCH_ATTRIBUTES,
            paged_size=500,
            generator=True
        )

        # Ergebnisse parsen
        member_list = []
        for entry in entry_generator:
            member_list.append(entry['attributes'])
        return member_list
