from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import random
import mysql.connector
from mysql.connector import Error
from functools import wraps

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

# Datenbank-Konfiguration
DB_CONFIG = {
    'host': '217.154.199.161',
    'user': 'n8n1',
    'password': 'Toastbrot',
    'database': 'n8n1',
    'port': 3306
}

def get_db_connection():
    """Erstellt eine Datenbankverbindung"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
        return None

def get_order_requests():
    """Holt alle Bestellanfragen aus der Datenbank"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orderrequestdata ORDER BY id DESC")
        requests = cursor.fetchall()
        return requests
    except Error as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_order_request(name, number, link, description, ki_description, urgency):
    """Fügt eine neue Bestellanfrage zur Datenbank hinzu"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
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
        
        values = (name, number, link, description, ki_description, urgency)
        cursor.execute(query, values)
        connection.commit()
        return True
    except Error as e:
        print(f"Fehler beim Hinzufügen der Daten: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_order_request(request_id, name, number, link, description, ki_description, urgency):
    """Aktualisiert eine bestehende Bestellanfrage in der Datenbank"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
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
        
        values = (name, number, link, description, ki_description, urgency, request_id)
        cursor.execute(query, values)
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Fehler beim Aktualisieren der Daten: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_order_request(request_id):
    """Löscht eine Bestellanfrage aus der Datenbank"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        query = "DELETE FROM orderrequestdata WHERE id = %s"
        cursor.execute(query, (request_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Fehler beim Löschen der Daten: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_order_request_by_id(request_id):
    """Holt eine einzelne Bestellanfrage anhand der ID"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orderrequestdata WHERE id = %s", (request_id,))
        request = cursor.fetchone()
        return request
    except Error as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

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

@app.route("/neue-anfrage", methods=["GET", "POST"])
def externe_anfrage():
    """Externe Seite zum Teilen - Formular für Prozess Automatisierung"""
    if request.method == "POST":
        name = request.form.get("name", "")
        company = request.form.get("company", "")
        contact = request.form.get("contact", "")
        link = request.form.get("link", "")
        description = request.form.get("description", "")
        
        # Kombiniere die Felder für die Datenbank
        full_name = f"{name} ({company})" if company else name
        ki_description = f"Kontakt: {contact}" if contact else ""
        number = ""  # Leer für Prozess-Anfragen
        urgency = 5  # Standardwert für externe Anfragen
        
        # In Datenbank speichern
        if add_order_request(full_name, number, link, description, ki_description, urgency):
            return render_template("externe_anfrage.html", success=True)
        else:
            return render_template("externe_anfrage.html", error=True)
    
    return render_template("externe_anfrage.html")

@app.route("/prozess-anfrage")
def prozess_anfrage():
    """Moderne Formular-Seite für n8n Webhook"""
    return render_template("workflow_form.html")

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
    app.run(debug=True, port="3000")