from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# Supabase Connection URL
DB_URL = "postgresql://postgres.xfdjisqkteygxzsssmtv:zVqBu5E*w2g$5Hp@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def get_db_connection():
    return psycopg2.connect(DB_URL)

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    new_token = data.get('token')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # මීට කලින් Save කරපු Token එක ගන්න
    cur.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1")
    last_token = cur.fetchone()
    
    status = "Changed"
    if last_token and last_token[0] == new_token:
        status = "Not Changed"
    
    # නව Token එක DB එකට දාන්න
    cur.execute("INSERT INTO tokens (token) VALUES (%s)", (new_token,))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        "status": status,
        "new_token": new_token,
        "old_token": last_token[0] if last_token else "No old token"
    })

if __name__ == '__main__':
    app.run()
