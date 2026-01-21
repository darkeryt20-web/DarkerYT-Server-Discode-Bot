import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os
from flask import Flask, render_template_string
from threading import Thread
from datetime import datetime

# --- Flask Web Server Setup ---
app = Flask(__name__)
member_data = [] # මෙතන තමයි විස්තර සේව් වෙන්නේ

@app.route('/')
def index():
    # වෙබ් අඩවියේ පෙනුම (Simple HTML Table)
    html = '''
    <html>
    <head>
        <title>Server Members Log</title>
        <style>
            body { font-family: Arial, sans-serif; background: #2c2f33; color: white; text-align: center; }
            table { width: 80%; margin: 20px auto; border-collapse: collapse; }
            th, td { border: 1px solid #444; padding: 10px; }
            th { background: #7289da; }
            img { border-radius: 50%; width: 40px; }
        </style>
    </head>
    <body>
        <h2>📥 Recent Joined Members</h2>
        <table>
            <tr>
                <th>Avatar</th>
                <th>Name</th>
                <th>Joined Time (UTC)</th>
            </tr>
            {% for member in data %}
            <tr>
                <td><img src="{{ member.avatar }}"></td>
                <td>{{ member.name }}</td>
                <td>{{ member.time }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(html, data=member_data)

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discord Bot Setup ---
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711

@bot.event
async def on_ready():
    print(f'✅ Bot and Web Server are running!')

@bot.event
async def on_member_join(member):
    # විස්තර ලැයිස්තුවට එකතු කිරීම
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    member_info = {
        "name": member.name,
        "avatar": member.display_avatar.url,
        "time": now
    }
    member_data.insert(0, member_info) # අලුත් අයව උඩටම දාන්න

    # Welcome Image කොටස (කලින් තිබුණු code එකම මෙතනට දාන්න)
    channel = bot.get_channel(WELCOME_CH_ID)
    if channel:
        await channel.send(f"Welcome {member.mention}! විස්තර වෙබ් එකට ඇඩ් වුණා.")

# Web Server එක පණ ගැන්වීම
keep_alive()
bot.run(TOKEN)
