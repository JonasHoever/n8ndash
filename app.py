from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import random
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

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
def dashboard():
    # Workflow-Statistiken aus Demo-Daten
    total_runs = sum(w["runs_today"] for w in workflows)
    active_count = sum(1 for w in workflows if w["active"])
    stopped_count = sum(1 for w in workflows if not w["active"])
    success_count = sum(1 for w in workflows if w["status"]=="success")
    error_count = sum(1 for w in workflows if w["status"]=="error")
    
    # Bestellanfragen aus der Datenbank
    order_requests = get_order_requests()
    
    return render_template(
        "dashboard.html", 
        workflows=workflows, 
        total_runs=total_runs,
        active_count=active_count,
        stopped_count=stopped_count,
        success_count=success_count,
        error_count=error_count,
        order_requests=order_requests
    )

@app.route("/toggle/<int:wf_id>", methods=["POST"])
def toggle_workflow(wf_id):
    for wf in workflows:
        if wf["id"] == wf_id:
            wf["active"] = not wf["active"]
            wf["status"] = "success" if wf["active"] else "stopped"
            break
    return jsonify({"success": True, "active": wf["active"], "status": wf["status"]})

@app.route("/workflow_requests", methods=["GET"])
def workflow_requests_view():
    """Interne Seite für Mitarbeiter - zeigt alle Bestellanfragen aus der Datenbank"""
    # Alle Bestellanfragen aus der Datenbank holen
    order_requests = get_order_requests()
    return render_template("workflow_requests.html", order_requests=order_requests)

@app.route("/neue-anfrage", methods=["GET", "POST"])
def externe_anfrage():
    """Externe Seite zum Teilen - Formular für neue Bestellanfragen"""
    if request.method == "POST":
        name = request.form.get("name", "")
        number = request.form.get("number", "")
        link = request.form.get("link", "")
        description = request.form.get("description", "")
        ki_description = request.form.get("ki_description", "")
        urgency = int(request.form.get("urgency", 1))
        
        # In Datenbank speichern
        if add_order_request(name, number, link, description, ki_description, urgency):
            return render_template("externe_anfrage.html", success=True)
        else:
            return render_template("externe_anfrage.html", error=True)
    
    return render_template("externe_anfrage.html")

@app.route("/prozess-anfrage")
def prozess_anfrage():
    """Moderne Formular-Seite für n8n Webhook"""
    return render_template("workflow_form.html")

@app.route("/admin", methods=["GET", "POST"])
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

if __name__ == "__main__":
    app.run(debug=True, port="3000")