import discord
from discord.ext import commands
import os
import threading
from flask import Flask

# --- Flask Health Check Server ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    # Koyeb requires port 8000 by default based on your spec
    app.run(host='0.0.0.0', port=8000)

# --- Discord Bot Setup ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()  # Required for Leveling, Member Count, etc.
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Startup Notification Channel
        self.startup_channel_id = 1474051484390789253
        
        # Load Cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded extension: {filename}')
                except Exception as e:
                    print(f'Failed to load extension {filename}: {e}')
        
        # Sync Slash Commands
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        
        # Send Startup Notification
        channel = self.get_channel(self.startup_channel_id)
        if channel:
            embed = discord.Embed(
                title="🚀 System Online",
                description="The bot has successfully started and is connected to Koyeb.",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)

# --- Execution ---
if __name__ == "__main__":
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start Discord Bot
    bot = MyBot()
    token = os.getenv('DISCORD_TOKEN')
    
    if token:
        bot.run(token)
    else:
        print("ERROR: DISCORD_TOKEN not found in environment variables.")
