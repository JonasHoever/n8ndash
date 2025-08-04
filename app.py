from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import random
import mysql.connector
from mysql.connector import Error, pooling
from functools import wraps
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Ändere dies für Produktion!

# Admin-Passwort (in Produktion sollte dies sicherer gespeichert werden)
ADMIN_PASSWORD = "admin123"

def login_required(f):
    """Decorator für passwortgeschützte Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Datenbank-Konfiguration mit Connection Pooling
DB_CONFIG = {
    'host': '217.154.199.161',
    'user': 'n8n1',
    'password': 'Toastbrot',
    'database': 'n8n1',
    'port': 3306,
    'pool_name': 'n8n_pool',
    'pool_size': 10,  # Anzahl der Verbindungen im Pool
    'pool_reset_session': True,
    'autocommit': True,  # Automatisches Commit für bessere Performance
    'connect_timeout': 5,  # Timeout für Verbindungsaufbau
    'sql_mode': 'TRADITIONAL',
    'charset': 'utf8mb4',
    'use_unicode': True
}

# Globaler Connection Pool
connection_pool = None
pool_lock = threading.Lock()
connection_stats = {
    'total_connections': 0,
    'active_connections': 0,
    'failed_connections': 0,
    'last_error': None
}

def initialize_connection_pool():
    """Initialisiert den Connection Pool"""
    global connection_pool
    try:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)
        print(f"✅ Datenbank Connection Pool initialisiert (Pool-Größe: {DB_CONFIG['pool_size']})")
        return True
    except Error as e:
        print(f"❌ Fehler beim Erstellen des Connection Pools: {e}")
        return False

def get_db_connection():
    """Holt eine Verbindung aus dem Connection Pool"""
    global connection_pool, connection_stats
    
    if connection_pool is None:
        with pool_lock:
            if connection_pool is None:
                if not initialize_connection_pool():
                    connection_stats['failed_connections'] += 1
                    return None
    
    try:
        connection = connection_pool.get_connection()
        # Kurzer Ping-Test um sicherzustellen, dass die Verbindung aktiv ist
        connection.ping(reconnect=True, attempts=3, delay=1)
        connection_stats['total_connections'] += 1
        connection_stats['active_connections'] += 1
        return connection
    except Error as e:
        print(f"❌ Fehler beim Abrufen der Datenbankverbindung: {e}")
        connection_stats['failed_connections'] += 1
        connection_stats['last_error'] = str(e)
        return None

def execute_query_safe(query, params=None, fetch_type='none'):
    """
    Sichere Ausführung von Datenbankabfragen mit automatischer Verbindungsverwaltung
    
    Args:
        query: SQL-Query als String
        params: Parameter für die Query (tuple oder None)
        fetch_type: 'all', 'one', 'none' (für SELECT, INSERT/UPDATE/DELETE)
    
    Returns:
        Ergebnis der Query oder None bei Fehler
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True if fetch_type != 'none' else False)
        
        # Query mit Timeout ausführen
        start_time = time.time()
        cursor.execute(query, params or ())
        
        # Bei SELECT-Queries: Daten abrufen
        if fetch_type == 'all':
            result = cursor.fetchall()
        elif fetch_type == 'one':
            result = cursor.fetchone()
        else:
            # Bei INSERT/UPDATE/DELETE: Commit und Anzahl betroffener Zeilen
            connection.commit()
            result = cursor.rowcount
        
        execution_time = time.time() - start_time
        if execution_time > 1.0:  # Warnung bei langsamen Queries
            print(f"⚠️ Langsame Datenbankabfrage: {execution_time:.2f}s - {query[:50]}...")
        
        return result
        
    except Error as e:
        print(f"❌ Datenbankfehler: {e}")
        if connection:
            try:
                connection.rollback()
            except:
                pass
        return None
    
    finally:
        # Verbindung sauber schließen
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            try:
                connection.close()
                connection_stats['active_connections'] = max(0, connection_stats['active_connections'] - 1)
            except:
                pass

def get_order_requests():
    """Holt alle Bestellanfragen aus der Datenbank"""
    query = "SELECT * FROM orderrequestdata ORDER BY id DESC"
    result = execute_query_safe(query, fetch_type='all')
    return result or []

def add_order_request(name, number, link, description, ki_description, urgency):
    """Fügt eine neue Bestellanfrage zur Datenbank hinzu"""
    query = """INSERT INTO orderrequestdata 
               (name, number, link, description, ki_description, urgency) 
               VALUES (%s, %s, %s, %s, %s, %s)"""
    
    # Behandle leere Strings als NULL
    name = name if name and name.strip() else None
    number = number if number and number.strip() else None
    link = link if link and link.strip() else None
    description = description if description and description.strip() else None
    ki_description = ki_description if ki_description and ki_description.strip() else None
    urgency = int(urgency) if urgency else None
    
    params = (name, number, link, description, ki_description, urgency)
    result = execute_query_safe(query, params, fetch_type='none')
    return result is not None and result > 0

def update_order_request(request_id, name, number, link, description, ki_description, urgency):
    """Aktualisiert eine bestehende Bestellanfrage in der Datenbank"""
    query = """UPDATE orderrequestdata 
               SET name = %s, number = %s, link = %s, description = %s, 
                   ki_description = %s, urgency = %s 
               WHERE id = %s"""
    
    # Behandle leere Strings als NULL
    name = name if name and name.strip() else None
    number = number if number and number.strip() else None
    link = link if link and link.strip() else None
    description = description if description and description.strip() else None
    ki_description = ki_description if ki_description and ki_description.strip() else None
    urgency = int(urgency) if urgency else None
    
    params = (name, number, link, description, ki_description, urgency, request_id)
    result = execute_query_safe(query, params, fetch_type='none')
    return result is not None and result > 0

def delete_order_request(request_id):
    """Löscht eine Bestellanfrage aus der Datenbank"""
    query = "DELETE FROM orderrequestdata WHERE id = %s"
    result = execute_query_safe(query, (request_id,), fetch_type='none')
    return result is not None and result > 0

def get_order_request_by_id(request_id):
    """Holt eine einzelne Bestellanfrage anhand der ID"""
    query = "SELECT * FROM orderrequestdata WHERE id = %s"
    return execute_query_safe(query, (request_id,), fetch_type='one')

def get_database_status():
    """Prüft den Status der Datenbank und des Connection Pools"""
    global connection_stats
    
    try:
        connection = get_db_connection()
        if not connection:
            return {
                "status": "error", 
                "message": "Keine Verbindung möglich",
                "stats": connection_stats
            }
        
        # Teste mit einfacher Query
        cursor = connection.cursor()
        start_time = time.time()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        query_time = time.time() - start_time
        
        cursor.close()
        connection.close()
        
        if result and result[0] == 1:
            status_msg = f"Verbunden (Antwortzeit: {query_time:.3f}s)"
            return {
                "status": "healthy", 
                "message": status_msg,
                "pool_size": DB_CONFIG.get('pool_size', 'unbekannt'),
                "stats": connection_stats,
                "response_time": query_time
            }
        else:
            return {
                "status": "warning", 
                "message": "Unerwartetes Ergebnis",
                "stats": connection_stats
            }
            
    except Exception as e:
        connection_stats['failed_connections'] += 1
        connection_stats['last_error'] = str(e)
        return {
            "status": "error", 
            "message": f"Verbindungsfehler: {str(e)}",
            "stats": connection_stats
        }

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login-Seite für Admin-Zugang"""
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error=True)
    
    # Wenn bereits eingeloggt, zur Dashboard weiterleiten
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout-Funktion"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Demo-Daten für Workflows (kann später auch in DB gespeichert werden)
workflows = [
    {
        "id": 1,
        "name": "CRM Sync",
        "active": True,
        "runs_today": random.randint(8, 30),
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success"
    },
    {
        "id": 2,
        "name": "Newsletter Trigger",
        "active": False,
        "runs_today": random.randint(0, 2),
        "last_run": "2025-08-01 15:22:12",
        "status": "stopped"
    },
    {
        "id": 3,
        "name": "Slack Alert",
        "active": True,
        "runs_today": random.randint(5, 18),
        "last_run": "2025-08-02 08:10:22",
        "status": "error"
    }
]

@app.route("/")
@login_required
def dashboard():
    # Bestellanfragen aus der Datenbank
    order_requests = get_order_requests()
    
    # Statistiken basierend auf echten Daten
    total_requests = len(order_requests)
    high_priority = sum(1 for req in order_requests if req.get('urgency', 0) and req['urgency'] >= 8)
    medium_priority = sum(1 for req in order_requests if req.get('urgency', 0) and 5 <= req['urgency'] < 8)
    low_priority = sum(1 for req in order_requests if req.get('urgency', 0) and req['urgency'] < 5)
    
    return render_template(
        "dashboard.html", 
        order_requests=order_requests,
        total_requests=total_requests,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority
    )

@app.route("/workflow_requests", methods=["GET"])
@login_required
def workflow_requests_view():
    """Interne Seite für Mitarbeiter - zeigt alle Bestellanfragen aus der Datenbank"""
    # Alle Bestellanfragen aus der Datenbank holen
    order_requests = get_order_requests()
    return render_template("workflow_requests.html", order_requests=order_requests)

@app.route("/neue-anfrage")
def externe_anfrage():
    """Externe Seite zum Teilen - Formular für Prozess Automatisierung (ohne Login-Pflicht)"""
    return render_template("externe_anfrage.html")

@app.route("/api/health")
def health_check():
    """API-Endpoint für Datenbank-Gesundheitsprüfung"""
    db_status = get_database_status()
    
    if db_status["status"] == "healthy":
        return jsonify(db_status), 200
    elif db_status["status"] == "warning":
        return jsonify(db_status), 206  # Partial Content
    else:
        return jsonify(db_status), 503  # Service Unavailable

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin_requests():
    if request.method == "POST":
        # Hier könnte man später eine Update-Funktion für die Datenbank implementieren
        req_id = int(request.form.get("req_id"))
        status = request.form.get("status")
        comment = request.form.get("admin_comment", "")
        # TODO: Update in Datenbank implementieren
        return redirect(url_for("admin_requests"))
    
    # Alle Bestellanfragen aus der Datenbank holen
    order_requests = get_order_requests()
    return render_template("admin.html", order_requests=order_requests)

@app.route("/admin/edit/<int:request_id>", methods=["GET", "POST"])
@login_required
def edit_request(request_id):
    """Bearbeite eine bestehende Bestellanfrage"""
    if request.method == "POST":
        name = request.form.get("name", "")
        number = request.form.get("number", "")
        link = request.form.get("link", "")
        description = request.form.get("description", "")
        ki_description = request.form.get("ki_description", "")
        urgency = request.form.get("urgency", 5)
        
        if update_order_request(request_id, name, number, link, description, ki_description, urgency):
            return redirect(url_for("admin_requests"))
        else:
            return render_template("edit_request.html", 
                                 request=get_order_request_by_id(request_id), 
                                 error=True)
    
    # GET: Zeige Bearbeitungsformular
    order_request = get_order_request_by_id(request_id)
    if not order_request:
        return redirect(url_for("admin_requests"))
    
    return render_template("edit_request.html", request=order_request)

@app.route("/admin/delete/<int:request_id>", methods=["POST"])
@login_required
def delete_request(request_id):
    """Lösche eine Bestellanfrage"""
    if delete_order_request(request_id):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Fehler beim Löschen"})

if __name__ == "__main__":
    # Initialisiere Connection Pool beim Start
    print("🚀 Starte n8n Dashboard...")
    if initialize_connection_pool():
        print("✅ Datenbank-Verbindung erfolgreich initialisiert")
        app.run(debug=True, port="3000", host="0.0.0.0")
    else:
        print("❌ Fehler beim Initialisieren der Datenbank - Server wird trotzdem gestartet")
        app.run(debug=True, port="3000", host="0.0.0.0")