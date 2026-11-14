import os
import time
import threading
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from bot import ClouskeeBot

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

START_TIME = time.time()
bot = ClouskeeBot()


def format_uptime(seconds: float) -> str:
    mins, sec = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days}d {hours}h {mins}m {sec}s"
    return f"{hours}h {mins}m {sec}s"


def get_bot_stats() -> dict:
    is_online = bot.is_ready() and not bot.is_closed()
    latency = round(bot.latency * 1000) if is_online and bot.latency == bot.latency else 0

    total_verified = sum(len(users) for users in bot.verified_users.values())
    connected_vcs = []
    for guild in bot.guilds:
        if guild.voice_client and guild.voice_client.channel:
            connected_vcs.append(f"{guild.voice_client.channel.name}")

    return {
        "status": "ONLINE" if is_online else "STARTING",
        "bot_name": str(bot.user) if bot.user else "Clouskee Security",
        "ping_ms": latency,
        "uptime": format_uptime(time.time() - START_TIME),
        "verified_users": total_verified,
        "servers": len(bot.guilds),
        "voice_channel": ", ".join(connected_vcs) if connected_vcs else "Not Connected",
        "port": 8000
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clouskee Security • Live Node Status</title>
    <style>
        :root {
            --bg: #090a0f;
            --card: rgba(18, 20, 29, 0.85);
            --border: rgba(255, 166, 0, 0.25);
            --accent: #ff9900;
            --accent-glow: rgba(255, 153, 0, 0.35);
            --green: #00ff88;
            --green-glow: rgba(0, 255, 136, 0.25);
            --text: #f3f4f6;
            --muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body {
            background: radial-gradient(circle at top right, #1a150e, var(--bg) 55%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 780px;
            background: var(--card);
            backdrop-filter: blur(14px);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 32px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.7), 0 0 30px rgba(255, 153, 0, 0.08);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 20px;
            margin-bottom: 26px;
        }
        .brand h1 {
            font-size: 1.65rem;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #ffbb00, #ff6b00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand p { color: var(--muted); font-size: 0.9rem; margin-top: 4px; }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid var(--green);
            color: var(--green);
            padding: 8px 18px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.9rem;
            box-shadow: 0 0 18px var(--green-glow);
        }
        .dot {
            width: 10px;
            height: 10px;
            background: var(--green);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(0, 255, 136, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            padding: 18px;
            transition: transform 0.2s, border-color 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            border-color: var(--accent);
        }
        .stat-label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.8px; }
        .stat-value { font-size: 1.35rem; font-weight: 700; margin-top: 8px; color: #fff; }
        .highlight { color: var(--accent); }
        .port-box {
            margin-top: 22px;
            background: rgba(255, 153, 0, 0.07);
            border: 1px dashed var(--border);
            border-radius: 12px;
            padding: 14px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            font-size: 0.9rem;
        }
        .port-box code {
            background: rgba(0,0,0,0.5);
            padding: 4px 10px;
            border-radius: 6px;
            color: var(--accent);
            font-family: monospace;
        }
        .footer {
            margin-top: 24px;
            text-align: center;
            color: var(--muted);
            font-size: 0.82rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="brand">
                <h1>🛡️ CLOUSKEE SECURITY</h1>
                <p id="bot-name">Initializing Node...</p>
            </div>
            <div class="status-badge">
                <span class="dot"></span>
                <span id="status-text">ONLINE</span>
            </div>
        </div>

        <div class="grid">
            <div class="stat-card">
                <div class="stat-label">Gateway Latency</div>
                <div class="stat-value highlight" id="ping">-- ms</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">System Uptime</div>
                <div class="stat-value" id="uptime">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Verified Members</div>
                <div class="stat-value highlight" id="verified">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">24/7 Voice Channel</div>
                <div class="stat-value" id="vc" style="font-size: 1.05rem;">--</div>
            </div>
        </div>

        <div class="port-box">
            <span>🌐 <strong>Active Health Port:</strong> <code id="port-num">0.0.0.0:8000</code></span>
            <span>🔗 <strong>Endpoint:</strong> <code id="host-url">/api/status</code></span>
        </div>

        <div class="footer">
            Developed By Clouskee • Auto-syncing live telemetry every 5 seconds
        </div>
    </div>

    <script>
        document.getElementById('host-url').textContent = window.location.origin + '/api/status';

        async function updateStats() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('status-text').textContent = data.status;
                document.getElementById('bot-name').textContent = data.bot_name + ' • Koyeb Cloud Instance';
                document.getElementById('ping').textContent = data.ping_ms + ' ms';
                document.getElementById('uptime').textContent = data.uptime;
                document.getElementById('verified').textContent = data.verified_users;
                document.getElementById('vc').textContent = data.voice_channel;
                document.getElementById('port-num').textContent = '0.0.0.0:' + data.port;
            } catch (e) {
                document.getElementById('status-text').textContent = 'RECONNECTING';
            }
        }
        updateStats();
        setInterval(updateStats, 5000);
    </script>
</body>
</html>
"""


async def handle_dashboard(request):
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def handle_api_status(request):
    return web.json_response(get_bot_stats())


async def start_services():
    # 1. Start Web Dashboard & Koyeb Health Check on Port 8000
    app = web.Application()
    app.router.add_get("/", handle_dashboard)
    app.router.add_get("/api/status", handle_api_status)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print("🌐 Dashboard & Health Check running on http://0.0.0.0:8000")

    # 2. Start Discord Bot
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable not found!")
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(start_services())
