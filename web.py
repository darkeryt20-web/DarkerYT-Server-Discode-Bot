from flask import Flask, render_template_string
import os

app = Flask(__name__)

@app.route('/')
def home():
    # මෙතන තියෙන්නේ ඔයාගේ වෙබ් අඩවියේ පෙනුම (HTML/CSS)
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DarkerYT Bot Dashboard</title>
        <style>
            body { background-color: #0f0f0f; color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #1a1a1a; padding: 2rem; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); border: 1px solid #333; text-align: center; width: 350px; }
            h1 { color: #5865F2; margin-bottom: 10px; }
            .status-container { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 20px; }
            .dot { height: 12px; width: 12px; background-color: #43b581; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #43b581; }
            p { color: #aaa; font-size: 0.9rem; }
            .footer { margin-top: 20px; font-size: 0.7rem; color: #555; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>DarkerYT Bot</h1>
            <p>High Performance Discord Bot</p>
            <div class="status-container">
                <div class="dot"></div>
                <span>Status: <b>Online</b></span>
            </div>
            <div style="margin-top: 20px; text-align: left; font-size: 0.8rem; background: #222; padding: 10px; border-radius: 5px;">
                <code>> main.py: Running<br>> verify.py: Running<br>> welcome.py: Running</code>
            </div>
            <div class="footer">Hosted on Koyeb | Port 8003</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_code)

if __name__ == "__main__":
    # Port එක 8003 ලෙස සෙට් කිරීම
    port = int(os.environ.get("PORT", 8003))
    app.run(host='0.0.0.0', port=port)
