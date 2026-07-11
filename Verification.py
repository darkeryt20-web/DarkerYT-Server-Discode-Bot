from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# DB URL එක Environment Variable එකෙන් ලබා ගැනීම (ආරක්ෂිතයි)
DB_URL = os.environ.get('DATABASE_URL')

def create_table():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # Table එක නොමැති නම් සාදන්න
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id SERIAL PRIMARY KEY,
                token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database table check/creation success!")
    except Exception as e:
        print(f"Error creating table: {e}")

# ඇප් එක පටන් ගන්නා විටම Table එක සාදන්න
create_table()

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    new_token = data.get('token')
    
    if not new_token:
        return jsonify({"status": "error", "message": "No token provided"}), 400

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # පැරණි token එක පරීක්ෂා කිරීම
        cur.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1")
        last_row = cur.fetchone()
        
        status = "Changed"
        if last_row and last_row[0] == new_token:
            status = "Not Changed"
        
        # නව එක insert කිරීම
        cur.execute("INSERT INTO tokens (token) VALUES (%s)", (new_token,))
        conn.commit()
        
        old_token = last_row[0] if last_row else "None"
        
        cur.close()
        conn.close()
        
        return jsonify({
            "status": status,
            "new_token": new_token,
            "old_token": old_token
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run()
