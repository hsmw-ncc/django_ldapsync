# LdapSync

## Allgemeines
* Django-Modul zum Synchronisieren der Nutzer mit dem LDAP/AD
* für jeden Nutzer der angelegt wird

## Einbinden in ein Django-Projekt
* requirements.txt
```
-e git+ssh://git@github.com:HSMW-NCC/django_hsmw_ldap_sync.git#egg=ldapsync
```
* `INSTALLED_APPS` erweitern
```python
INSTALLED_APPS = (
    ...
    'ldapsync',
)
```
* Einstellungen des Moduls in den Django-Settings ablegen
```python
LDAP = {
    'uri': 'ldaps://server/OU=Users,OU=HS,DC=hs-mittweida,DC=de',
    'username': 'xxxxxxxxxxx',
    'password': 'xxxxxxxxxxx',
    'timeout': 3
}
LDAP_SYNC_DISABLE_INVALID_USER=True
```

## Einstellungen
`LDAP`
* `uri` - LDAP-Pfad: Protokoll, Server, SearchBase
* `username` - Benutzername (AD)
* `password` - Zugehöriges Passwort
* `timeout` - Timeout in Sekunden

`LDAP_SYNC_DISABLE_INVALID_USER`
* wenn `True` werden nicht gefundene Nutzer auf inaktiv gesetzt

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