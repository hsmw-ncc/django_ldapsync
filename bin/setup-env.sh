#!/bin/bash
# Skript zur Einrichtung und zur Aktualisierung der Anwendung

# Update unter Debian
SCRIPT_BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_BASE="$(dirname "$SCRIPT_BASE")"

# ENV-Verzeichnis ggf. erstellen
echo -e "\r\n\r\n>>>>> Virtuelle Umgebung prüfen"
if [[ ! -e ./venv/bin/ ]]; then
  rm -rf ./venv
  python3 -m venv venv
fi

# Abhängigkeiten installieren
echo -e "\r\n\r\n>>>>> Abhängigkeiten installieren"
./venv/bin/python3 -m pip install --upgrade pip
./venv/bin/pip3 install --no-cache-dir --isolated --upgrade -r requirements.txt
./venv/bin/pip3 freeze > installed.txt
