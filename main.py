import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask
from datetime import datetime

# --- Health Check ---
app = Flask(__name__)
@app.route('.')
def health(): return "OK", 200

def run_web(): app.run(host='0.0.0.0', port=8000)

# --- Bot Logic ---
class HighPerformanceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 1. 'cogs' folder eke thiyena ewa load kireema
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f"✅ Loaded Cog: {filename}")
                    except Exception as e:
                        print(f"❌ Failed to load Cog {filename}: {e}")
        
        # 2. 'welcome.py' eka main folder eke thibbath eka load kireema
        if os.path.exists('./welcome.py'):
            try:
                await self.load_extension('welcome')
                print("✅ Loaded welcome.py from Root")
            except Exception as e:
                print(f"❌ Failed to load welcome.py: {e}")

        # 3. Slash commands sync kireema
        await self.tree.sync()
        print("🔄 Slash Commands Synced")

    async def on_ready(self):
        print(f'🚀 {self.user} is online.')
        channel = self.get_channel(1474051484390789253)
        
        if channel:
            now = datetime.now()
            current_time = now.strftime("%I:%M %p")
            current_date = now.strftime("%Y-%m-%d")
            
            embed = discord.Embed(
                title="🟢 System Online",
                description="The bot has been successfully deployed and is now active.",
                color=discord.Color.green()
            )
            embed.add_field(name="📅 Start Date", value=current_date, inline=True)
            embed.add_field(name="⏰ Start Time", value=current_time, inline=True)
            
            image_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_312ul4312ul4312u.png"
            embed.set_image(url=image_url)
            embed.set_footer(text="Performance Node: Koyeb-1 • Status: Running")
            
            await channel.send(embed=embed)

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    bot = HighPerformanceBot()
    async with bot:
        token = os.getenv('DISCORD_TOKEN')
        if token:
            await bot.start(token)
        else:
            print("CRITICAL: DISCORD_TOKEN is missing!")

if __name__ == "__main__":
    asyncio.run(main())

