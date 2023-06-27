from io import StringIO
from django.conf import settings
from django.core import management
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

class LdapTestCase(TestCase):
    def setUp(self):
        self.USER_MODEL = get_user_model()
        self.client = Client(REMOTE_USER=settings.LDAP_TEST['username'])

    def test_sync_attributes(self):
        ''' Normalen Sync prüfen'''

        # User anlegen -> Sync sollte automatisch funktionieren
        user = self.USER_MODEL.objects.create(username=settings.LDAP_TEST['username'])
        self.assertEquals(user.first_name, settings.LDAP_TEST['expected_firstname'])
        self.assertEquals(user.last_name, settings.LDAP_TEST['expected_lastname'])
        self.assertNotEqual(user.email, '')

        # User abrufen -> Attribute sollten noch stimmen
        user = self.USER_MODEL.objects.get(username=settings.LDAP_TEST['username'])
        self.assertEquals(user.first_name, settings.LDAP_TEST['expected_firstname'])
        self.assertEquals(user.last_name, settings.LDAP_TEST['expected_lastname'])
        self.assertNotEqual(user.email, '')

    def test_autocreate(self):
        ''' Beim Einloggen wird der Nutzer automatisch angelegt'''

        # Einloggen simulieren
        response = self.client.get('/admin/')
        self.assertEquals(response.status_code, 302)

        # Sync sollte passiert sein
        user = self.USER_MODEL.objects.get(username=settings.LDAP_TEST['username'])
        self.assertEquals(user.first_name, settings.LDAP_TEST['expected_firstname'])
        self.assertEquals(user.last_name, settings.LDAP_TEST['expected_lastname'])
        self.assertNotEqual(user.email, '')

    def test_management_command(self):
        ''' Management-Commando testen '''

        # Nuter importieren anlegen
        management.call_command('ldap_import', group=settings.LDAP_TEST['expected_group'])

        # Sync ausführen, danach sollten die Attribute da sein
        management.call_command('ldap_sync')
        user = self.USER_MODEL.objects.get(username=settings.LDAP_TEST['username'])
        self.assertEquals(user.first_name, settings.LDAP_TEST['expected_firstname'])
        self.assertEquals(user.last_name, settings.LDAP_TEST['expected_lastname'])
        self.assertNotEqual(user.email, '')

    def test_management_command_is_active(self):
        ''' Management-Commando testen, Nicht gefundene Nutzer deaktivieren'''

        with self.settings(LDAP_SYNC_DISABLE_INVALID_USER=True):
            # Nutzer erstellen, Nutzer 1 ist im LDAP vorhanden, Nutzer 2 nicht
            self.USER_MODEL.objects.create(username=settings.LDAP_TEST['username'],  is_active=True)
            self.USER_MODEL.objects.create(username='not_in_ldap', is_active=True)

            # Attribute leeren
            self.USER_MODEL.objects.all().update(first_name='', last_name='', email='')

            # Synchronisation durchführen, Nutzer 1 ist aktiv, Nutzer 2 nicht
            management.call_command('ldap_sync')
            user = self.USER_MODEL.objects.get(username=settings.LDAP_TEST['username'])
            self.assertTrue(user.is_active)
            user = self.USER_MODEL.objects.get(username='not_in_ldap')
            self.assertFalse(user.is_active)

    def test_management_command_without_is_active_sync(self):
        ''' Management-Commando testen, Nicht gefundene Nutzer aktiv lassen'''

        with self.settings(LDAP_SYNC_DISABLE_INVALID_USER=False):
            # Nutzer erstellen, Nutzer 1 ist im LDAP vorhanden, Nutzer 2 nicht
            self.USER_MODEL.objects.create(username=settings.LDAP_TEST['username'],  is_active=True)
            self.USER_MODEL.objects.create(username='not_in_ldap', is_active=True)

            # Attribute leeren
            self.USER_MODEL.objects.all().update(first_name='', last_name='', email='')

            # Synchronisation durchführen, alle Nutzer sollten noch aktiv sein
            management.call_command('ldap_sync')
            user = self.USER_MODEL.objects.get(username=settings.LDAP_TEST['username'])
            self.assertTrue(user.is_active)
            user = self.USER_MODEL.objects.get(username='not_in_ldap')
            self.assertTrue(user.is_active)

    def test_management_command_exclude_arguments(self):
        ''' Management-Commando testen, bestimmte Nicht gefundene Nutzer ausnehmen'''

        with self.settings(LDAP_SYNC_DISABLE_INVALID_USER=True):
            # Nutzer erstellen, Nutzer 1 ist im LDAP vorhanden, Nutzer 2/3 nicht
            self.USER_MODEL.objects.create(username=settings.LDAP_TEST['username'],  is_active=False)
            self.USER_MODEL.objects.create(username='alice', is_active=False)
            self.USER_MODEL.objects.create(username='api-not_in_ldap', is_active=True)

            # Attribute leeren
            self.USER_MODEL.objects.all().update(first_name='', last_name='', email='')

            # Synchronisation durchführen
            stdout = StringIO()
            management.call_command('ldap_sync', exclude=['alice'], verbosity=3, stdout=stdout)

            # Status der Nutzer prüfen
            user = self.USER_MODEL.objects.get(username=settings.LDAP_TEST['username'])
            self.assertTrue(user.is_active)
            user = self.USER_MODEL.objects.get(username='alice')
            self.assertFalse(user.is_active)
            user = self.USER_MODEL.objects.get(username='api-not_in_ldap')
            self.assertTrue(user.is_active)

            # Output prüfen
            output_lines = set(stdout.getvalue().splitlines())
            self.assertIn("Ignoring api-not_in_ldap", output_lines)
            self.assertIn("Ignoring alice", output_lines)

    def test_invalid_user(self):
        ''' Ungültiger Nutzer anlegen '''

        self.USER_MODEL.objects.create(username='unknown')
        user = self.USER_MODEL.objects.get(username='unknown')
        self.assertEquals(user.first_name, '')
        self.assertEquals(user.last_name, '')
        self.assertEquals(user.email, '')
