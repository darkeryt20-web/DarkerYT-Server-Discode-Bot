import os
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bot_registry import ACTIVE_BOTS

# ==================== CYBERPUNK WEB DASHBOARD ====================
class CyberpunkDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # HTML Dashboard design (Clouskee Cyberpunk Theme)
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Clouskee Bot Core • Dashboard</title>
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                body {{ background-color: #0b0b0c; color: #f0f0f0; display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; }}
                .container {{ background: rgba(20, 20, 25, 0.85); border: 2px solid #ffb703; border-radius: 12px; padding: 40px; width: 600px; box-shadow: 0 0 30px rgba(255, 183, 3, 0.2); text-align: center; }}
                h1 {{ color: #ffb703; font-size: 28px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; }}
                .subtitle {{ color: #fb8500; font-size: 14px; margin-bottom: 30px; font-weight: 600; }}
                .status-box {{ background: #16161d; border-left: 5px solid #00ff88; padding: 15px; border-radius: 6px; text-align: left; margin-bottom: 25px; }}
                .status-row {{ display: flex; justify-content: space-between; margin: 8px 0; font-size: 15px; }}
                .status-badge {{ background: #00ff88; color: #000; padding: 2px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; }}
                .bots-list {{ text-align: left; background: #16161d; padding: 15px; border-radius: 6px; border: 1px solid #333; }}
                .bot-item {{ color: #00b4d8; font-family: monospace; margin: 5px 0; font-size: 14px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚡ Clouskee Core Hub</h1>
                <div class="subtitle">Next-Gen Bot Hosting & Security Grid</div>
                
                <div class="status-box">
                    <div class="status-row"><span>System Status:</span> <span class="status-badge">ONLINE</span></div>
                    <div class="status-row"><span>Health Check Port:</span> <b>8000 (Active)</b></div>
                    <div class="status-row"><span>Environment:</span> <b>Koyeb Cloud Free Tier</b></div>
                </div>

                <div class="bots-list">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #ffb703;">🤖 Active Loaded Bots:</div>
                    {''.join([f'<div class="bot-item">🟢 {bot}</div>' for bot in ACTIVE_BOTS])}
                </div>

                <div class="footer">Developed By Clouskee • Secured Gateway</div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Clean console output

def run_dashboard():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, CyberpunkDashboardHandler)
    print("🌐 Clouskee Cyberpunk Dashboard started on port 8000")
    httpd.serve_forever()

# ==================== MULTI-BOT RUNNER ====================
def run_bot(bot_filename):
    print(f"🚀 Launching bot process: {bot_filename}")
    subprocess.run(["python", bot_filename])

if __name__ == "__main__":
    # 1. Start Web Dashboard in a background thread (Koyeb Health Check)
    threading.Thread(target=run_dashboard, daemon=True).start()

    # 2. Start all active bots listed in bot_registry.py as separate threads/processes
    bot_threads = []
    for bot_file in ACTIVE_BOTS:
        if os.path.exists(bot_file):
            t = threading.Thread(target=run_bot, args=(bot_file,), daemon=True)
            t.start()
            bot_threads.append(t)
        else:
            print(f"❌ Error: Bot file '{bot_file}' not found in directory!")

    # Keep main process alive
    for t in bot_threads:
        t.join()
