# N8N Dashboard

Ein Flask-basiertes Dashboard für die Verwaltung von Prozess-Automatisierungsanfragen mit MySQL-Datenbankanbindung.

## Features

- 🔐 **Passwort-geschützter Admin-Bereich**
- 📊 **Dashboard mit Statistiken** über Anfragen
- 📝 **Öffentliches Formular** für Prozess-Automatisierungsanfragen
- ✏️ **CRUD-Operationen** für Admin-Verwaltung
- 🗄️ **MySQL-Datenbankintegration**
- 🎨 **Responsive Design** mit Bootstrap

## Schnellstart

### 1. Repository klonen
```bash
git clone <your-repository-url>
cd n8ndash
```

### 2. Automatische Installation und Start
```bash
./start.sh
```

Das Script erstellt automatisch eine virtuelle Umgebung, installiert alle Abhängigkeiten und startet die Anwendung.

### 3. Zugriff auf die Anwendung

- **Dashboard**: http://127.0.0.1:3000 (Login erforderlich)
- **Öffentliches Formular**: http://127.0.0.1:3000/prozess-anfrage
- **Admin-Login**: Passwort = `admin123`

## Manuelle Installation

Falls Sie das Start-Script nicht verwenden möchten:

```bash
# Virtuelle Umgebung erstellen
python3 -m venv .venv

# Virtuelle Umgebung aktivieren
source .venv/bin/activate  # macOS/Linux
# oder
.venv\Scripts\activate     # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python app.py
```

## Datenbankverbindung

Die Anwendung verbindet sich mit einer externen MySQL-Datenbank:
- Host: 217.154.199.161
- Datenbank: n8n1
- Tabelle: orderrequestdata

## Projektstruktur

```
n8ndash/
├── app.py                 # Haupt-Flask-Anwendung
├── start.sh              # Automatisches Setup-Script
├── requirements.txt      # Python-Abhängigkeiten
├── README.md            # Diese Datei
├── .gitignore           # Git-Ignore-Regeln
└── templates/           # HTML-Templates
    ├── dashboard.html      # Admin-Dashboard
    ├── login.html          # Login-Seite
    ├── admin.html          # Admin-Verwaltung
    ├── externe_anfrage.html # Öffentliches Formular
    └── ...
```

## Sicherheitshinweise

⚠️ **Für Produktionsumgebung ändern:**
- `app.secret_key` in `app.py`
- `ADMIN_PASSWORD` in `app.py`
- HTTPS verwenden
- Datenbankzugangsdaten in Umgebungsvariablen

## Technologien

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5.3.3, Animate.css, Font Awesome
- **Datenbank**: MySQL
- **Authentication**: Session-basiert

## Lizenz

Dieses Projekt ist für interne Nutzung bestimmt.
