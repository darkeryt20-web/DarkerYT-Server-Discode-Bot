from flask import Flask, render_template_string, request
import os
import threading
import subprocess
# web.py ඇතුළේ තිබුණ පරණ import අයින් කරලා මේක විතරක් දාන්න
from shared_data import bot_stats, verify_stats, welcome_stats

app = Flask(__name__)

# --- Dashboard UI (HTML/CSS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SXD Bot Ecosystem Control</title>
    <style>
        :root { --bg: #0b0e11; --card: #15191c; --primary: #5865F2; --green: #43b581; --red: #f04747; }
        body { background: var(--bg); color: #e3e5e8; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
        .card { background: var(--card); border-radius: 12px; padding: 20px; border: 1px solid #2f3136; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .status-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .online { background: rgba(67, 181, 129, 0.2); color: var(--green); }
        .offline { background: rgba(240, 71, 71, 0.2); color: var(--red); }
        h1 { text-align: center; color: var(--primary); }
        .stat-val { font-size: 24px; font-weight: bold; color: #fff; }
        .btn { background: var(--primary); color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; font-weight: bold; }
        .btn-restart { background: #4f545c; }
        .footer { text-align: center; margin-top: 50px; color: #72767d; font-size: 14px; }
    </style>
</head>
<body>
    <h1>SXD Bot Control Panel</h1>
    <div class="grid">
        <div class="card">
            <div style="display: flex; justify-content: space-between;">
                <h3>Core System</h3>
                <span class="status-badge {{ 'online' if main_stats.status == 'Online' else 'offline' }}">{{ main_stats.status }}</span>
            </div>
            <p>Servers: <span class="stat-val">{{ main_stats.servers }}</span></p>
            <p>Latency: <span class="stat-val">{{ main_stats.latency }}</span></p>
            <p>Last Sync: {{ main_stats.last_update }}</p>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between;">
                <h3>Shield Verification</h3>
                <span class="status-badge {{ 'online' if verify_stats.status == 'Online' else 'offline' }}">{{ verify_stats.status }}</span>
            </div>
            <p>Bot Name: {{ verify_stats.name }}</p>
            <p>Active Since: {{ verify_stats.last_run }}</p>
            <button class="btn btn-restart" onclick="location.href='/restart'">Restart Shield</button>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between;">
                <h3>Premium Welcomer</h3>
                <span class="status-badge {{ 'online' if welcome_stats.status == 'Online' else 'offline' }}">{{ welcome_stats.status }}</span>
            </div>
            <p>Welcomes Sent: <span class="stat-val">{{ welcome_stats.welcomes_sent }}</span></p>
            <p>Last User: <span style="color: var(--primary)">{{ welcome_stats.last_welcome }}</span></p>
        </div>
    </div>

    <div class="footer">
        Monitoring active on Port {{ port }}<br>
        Powered by DarkerYT & SXD VPN
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(
        HTML_TEMPLATE, 
        main_stats=bot_stats, 
        verify_stats=verify_stats, 
        welcome_stats=welcome_stats,
        port=8003
    )

@app.route('/restart')
def restart():
    os._exit(1) # This forces Koyeb to restart the entire container

def run():
    port = int(os.environ.get("PORT", 8003))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    run()
