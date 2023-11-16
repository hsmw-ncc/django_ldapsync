import os
import logging
import django
from django_ldapsync import Ldap

# Logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

# Minimale Django-Umgebung
os.environ['DJANGO_SETTINGS_MODULE'] = 'test.settings'
django.setup()

# Nutzer abrufen und ausgeben
ldap = Ldap()
if not ldap.connection:
  print("Konnte keine Verbindung herstellen")
  quit()
user = ldap.get_user(input("Benutzername: "))
for key in user:
  print(f"{key}: {user[key]}")

# Gruppe abrufen und ausgeben
group_dn = ldap.get_dn(input("Gruppenname: "))
members = ldap.get_group_members(group_dn)
for m in members:
  print(f"{m[ldap.get_username_key()]}: {m}")
