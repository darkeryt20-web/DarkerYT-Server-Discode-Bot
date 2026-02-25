import discord
from discord.ext import commands
import os
import threading
import logging
from flask import Flask

# Setup logging to see errors in Koyeb logs
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Create cogs directory if it doesn't exist to prevent crash
        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
            logging.info("Created missing 'cogs' directory.")

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                logging.info(f'Loaded: {filename}')
        
        await self.tree.sync()

if __name__ == "__main__":
    # 1. Start Health Check
    threading.Thread(target=run_flask, daemon=True).start()
    logging.info("Flask Health Check started on port 8000")

    # 2. Start Bot
    bot = MyBot()
    token = os.getenv('DISCORD_TOKEN')
    
    if token:
        logging.info("Token found, starting bot...")
        bot.run(token)
    else:
        logging.error("CRITICAL: DISCORD_TOKEN environment variable is missing!")
        # We don't want Code 0 here, so we keep the process alive 
        # for a bit so you can see the error in the logs.
        import time
        time.sleep(10)
