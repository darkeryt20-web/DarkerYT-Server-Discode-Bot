import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask

# --- Health Check ---
app = Flask(__name__)
@app.route('/')
def health(): return "OK", 200

def run_web(): app.run(host='0.0.0.0', port=8000)

# --- Bot Logic ---
class HighPerformanceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Create cogs folder if it doesn't exist
        if not os.path.exists('./cogs'): os.makedirs('./cogs')
        
        # Load extensions
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        await self.tree.sync()

    async def on_ready(self):
        print(f'🚀 {self.user} is online.')
        channel = self.get_channel(1474051484390789253)
        if channel:
            embed = discord.Embed(title="🟢 System Online", color=discord.Color.green())
            embed.set_footer(text="Performance Node: Koyeb-1")
            await channel.send(embed=embed)

async def main():
    # Start Flask thread
    threading.Thread(target=run_web, daemon=True).start()
    
    bot = HighPerformanceBot()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())
