import discord
import os
import threading
from discord.ext import commands
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

# --- Flask Server for Koyeb Health Checks ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

# --- Bot Configuration ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # List of Cogs to load (We will create these files next)
        initial_extensions = [
            'cogs.verification',
            'cogs.leveling',
            'cogs.music',
            'cogs.stats',
            'cogs.security',
            'cogs.welcome',
            'cogs.monitor'
        ]
        
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"Successfully loaded {ext}")
            except Exception as e:
                print(f"Failed to load {ext}: {e}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

if __name__ == "__main__":
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Run the Bot
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: No DISCORD_TOKEN found in environment variables.")
