# Django LdapSync

## Allgemeines
* Django-Modul zum Synchronisieren der Nutzer mit dem LDAP/AD
* für jeden Nutzer der angelegt wird

## Einbinden in ein Django-Projekt
* requirements.txt
```
-e git+https://github.com/HSMW-NCC/django_ldapsync.git#egg=django_ldapsync
```
* `INSTALLED_APPS` erweitern
```python
INSTALLED_APPS = (
    ...
    'django_ldapsync',
)
```
* Einstellungen des Moduls in den Django-Settings ablegen
```python
# LDAP-Verbindungsdaten
LDAP_SYNC_CONNECTION = {
    'uri': 'ldaps://server/OU=Users,OU=HS,DC=hs-mittweida,DC=de',
    'username': 'xxxxxxxxxxx',
    'password': 'xxxxxxxxxxx',
    # optionale Parameter
    'timeout': 5
}

# Welche Attribute sollen synchronisiert werden
# (Mapping mit Django)
LDAP_SYNC_USER_ATTRIBUTES = {
    'username': 'sAMAccountName',
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}

# Sollen nicht gefundene Nutzer deaktiviert werden?
LDAP_SYNC_DISABLE_INVALID_USER = True

# Nutzername immer in Kleinbuchstaben anlegen?
LDAP_SYNC_ALWAYS_LOWER_USERNAME = False
```

## Einstellungen
`LDAP_SYNC_CONNECTION`
* `uri` - LDAP-Pfad: Protokoll, Server, SearchBase
* `username` - Benutzername (AD)
* `password` - Zugehöriges Passwort
* `timeout` - Timeout in Sekunden

`LDAP_SYNC_USER_ATTRIBUTES`
* Mapping von Django auf LDAP
* Default siehe oben

`LDAP_SYNC_DISABLE_INVALID_USER`
* wenn `True` ann werden nicht gefundene Nutzer deaktiviert
* Default: `False`

`LDAP_SYNC_ALWAYS_LOWER_USERNAME`
* wenn `True` dann wird der Nutzername in Kleinbuchstaben umgewandelt
* wenn `False` dann wird der Nutzername ohne Änderung aus dem LDAP übernommen
* Default: `True`

## Import von Gruppen
* um Benutzer aus einer LDAP-Gruppe zu importieren
```
./venv/bin/python3 ./manage.py ldap_import --group <groupname>
```
* Nutzer werden mit LDAP-Attributen angelegt
* Sinnvoll in Kombination mit der Synchronisation

## Wiederkehrende Synchronisation
* um die Benutzer in regelmässigen Abständen zu Synchronisieren gibt es das Django-Kommando
```
./venv/bin/python3 ./manage.py ldap_sync
```
* Nutzer mit `api-` am Anfang werden standardmäßig ignoriert (siehe Parameter)
* Parameter
  * `--exclude` - Diese Nutzer nicht deaktivieren
  * `--exclude-regex` - Die Nutzer auf die der RegEx passt nicht deaktivieren (Default: `r'^api-'`)
  * die Parameter haben nur einen Effekt wenn `LDAP_SYNC_DISABLE_INVALID_USER=True` ist

# Entwicklung/Test
* Benötigte Pakete (Debian)
```bash
apt-get install git python3 python3-venv
```
* Testumgebung einrichten über `./bin/setup-env.sh`
* Nutzer und Passwort ablegen unter `local.py` ([Vorlage](./local-example.py))
* direkten Test der Ldap-Abfrage
```bash
source ./venv/bin/activate
python3 ./test_ldap.py
```
* kompletten Funktionstest des Moduls
```bash
source ./venv/bin/activate
python3 ./test_module.py
```
