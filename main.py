import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask

# --- Flask Health Check ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is alive!", 200

def run_web():
    # Koyeb requires port 8000 by default
    app.run(host='0.0.0.0', port=8000)

# --- Discord Bot ---
class HighPerformanceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # welcome.py load kireema
        if os.path.exists('./welcome.py'):
            try:
                await self.load_extension('welcome')
                print("✅ Welcome system loaded.")
            except Exception as e:
                print(f"❌ Welcome error: {e}")
        
        await self.tree.sync()
        print("🔄 Slash commands synced.")

    async def on_ready(self):
        print(f'🚀 Logged in as {self.user}')
        # Status channel message
        channel = self.get_channel(1474051484390789253)
        if channel:
            await channel.send("🟢 **SXD System Online!** Commands are ready.")

async def main():
    # Flask thread eka start kireema
    threading.Thread(target=run_web, daemon=True).start()
    
    bot = HighPerformanceBot()
    async with bot:
        token = os.getenv('DISCORD_TOKEN')
        if token:
            await bot.start(token)
        else:
            print("❌ Error: DISCORD_TOKEN is missing in Koyeb settings!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
