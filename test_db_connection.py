import mysql.connector

try:
    conn = mysql.connector.connect(
        host='217.154.199.161',
        user='n8n1',
        password='Toastbrot',
        database='n8n1',
        port=3306,
        connection_timeout=5
    )
    print('Verbindung erfolgreich!')
    conn.close()
except mysql.connector.Error as err:
    print(f'Fehler beim Verbinden: {err}')
