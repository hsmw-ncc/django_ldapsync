import logging
import ssl

import ldap3
from ldap3 import Server, Connection, SYNC, OFFLINE_SLAPD_2_4, MOCK_SYNC
from ldap3.core.exceptions import LDAPException
from ldap3.core.tls import Tls
from ldap3.utils.uri import parse_uri
from ldap3.utils.conv import escape_filter_chars

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

DEFAULT_LDAP_SYNC_USER_ATTRIBUTES = {
    'givenName': 'first_name',
    'sn': 'last_name',
    'mail': 'email',
}

logger = logging.getLogger(__name__)


class Ldap(object):
    def __init__(self):
        ''' Modul initialisieren'''

        # Einstellungen aus den Django-Settings übernehen
        self.LDAP_SYNC_URI = settings.LDAP['uri']
        self.LDAP_PARAMS   = parse_uri(self.LDAP_SYNC_URI)
        self.LDAP_SYNC_BASE_USER = settings.LDAP['username']
        self.LDAP_SYNC_BASE_PASS = settings.LDAP['password']
        self.LDAP_SYNC_USER_ATTRIBUTES = getattr(settings.LDAP, 'sync_user_attributes', DEFAULT_LDAP_SYNC_USER_ATTRIBUTES)
        self.LDAP_TIMEOUT = settings.LDAP['timeout']

        # Die maximale Länge der Felder bestimmen
        User = get_user_model()
        self.USER_MODEL_ATTRS_MAX_LENGTH = {}
        for field_name in self.LDAP_SYNC_USER_ATTRIBUTES.values():
            field = User._meta.get_field(field_name)
            self.USER_MODEL_ATTRS_MAX_LENGTH[field_name] = field.max_length

    @cached_property
    def connection(self):
        ''' Verbindung herstellen '''

        # Verbindungsparameter für den LDAP-Server
        server_kwargs = {
            'host': self.LDAP_PARAMS['host'],
            'use_ssl': False,
            'port': self.LDAP_PARAMS['port'],
            'connect_timeout': self.LDAP_TIMEOUT,
        }
        if self.LDAP_PARAMS['ssl']:
            server_kwargs['use_ssl'] = True
            server_kwargs['tls'] = Tls(validate=ssl.CERT_REQUIRED)

        # Authentifizierung am Server
        s = Server(**server_kwargs)
        connection_kwargs = {
            'server': s,
            'auto_bind': True,
            'user': self.LDAP_SYNC_BASE_USER,
            'password': self.LDAP_SYNC_BASE_PASS,
            'client_strategy': SYNC,
        }
        try:
            return Connection(**connection_kwargs)
        except LDAPException:
            logger.warning("LDAP connection failed, LDAP updates will not be available.")
            return None

    def get_attributes(self, username):
        """
        :attention: This method is not part of the public API. Do not use it.
        """
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
        """
        Returns the specified user from LDAP, without doing any conversion.

        :rtype: dict
        """
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
            logger.debug("Suche Nutzer: " + username)
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
