import discord
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 1. KOYEB HEALTH CHECK (FLASK) ---
app = Flask('')
@app.route('/')
def home(): return "I am alive!"

def run_web_server():
    app.run(host='0.0.0.0', port=8000)

# --- 2. CONFIGURATION ---
# Koyeb Environment Variables වල 'DISCORD_TOKEN' කියලා නම දීලා ටෝකන් එක දාන්න
TOKEN = os.getenv('DISCORD_TOKEN') 
LOG_CHANNEL_ID = 1464920331461328958 

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"❌ Sync error: {e}")

async def load_extensions():
    # මේ extensions (level.py, music.py, etc.) ඔයාගේ GitHub එකේ තිබිය යුතුයි
    extensions = ["level", "music", "welcome", "leave", "antilink"]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded: {ext}")
        except Exception as e:
            print(f"❌ Error loading {ext}: {e}")

async def main():
    # Web server එක background එකේ පටන් ගන්නවා
    Thread(target=run_web_server).start()
    
    async with bot:
        await load_extensions()
        if TOKEN:
            await bot.start(TOKEN)
        else:
            print("❌ Token Not Found! Koyeb Environment Variables වල 'DISCORD_TOKEN' දාන්න.")

if __name__ == "__main__":
    asyncio.run(main())
