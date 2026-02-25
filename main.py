import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask
from datetime import datetime, timedelta

# --- Health Check ---
app = Flask(__name__)
@app.route('/')
def health(): return "OK", 200
def run_web(): app.run(host='0.0.0.0', port=8000)

# --- Bot Logic ---
class HighPerformanceBot(commands.Bot):
    def __init__(self):
        # Ensure ALL intents are enabled in Developer Portal (General, Guilds, Messages)
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        if not os.path.exists('./cogs'): os.makedirs('./cogs')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
        await self.tree.sync()

    async def on_ready(self):
        print(f'🚀 {self.user} is online.')
        
        CHANNEL_ID = 1474051484390789253
        
        try:
            # Using fetch_channel is more reliable than get_channel on startup
            channel = await self.fetch_channel(CHANNEL_ID)
            
            # --- Time and Date calculations ---
            # Adjusted by +4 hours and 30 minutes
            adjusted_now = datetime.now() + timedelta(hours=4, minutes=30)
            current_time = adjusted_now.strftime("%I:%M %p")
            current_date = adjusted_now.strftime("%Y-%m-%d")
            
            # Embed Card Setup
            embed = discord.Embed(
                title="🟢 System Online",
                description="The bot has been successfully deployed and is now active.",
                color=discord.Color.green()
            )
            embed.add_field(name="📅 Start Date", value=f"`{current_date}`", inline=True)
            embed.add_field(name="⏰ Start Time (+4:30)", value=f"`{current_time}`", inline=True)
            
            image_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_312ul4312ul4312u.png"
            embed.set_image(url=image_url)
            embed.set_footer(text="Powered By SXD • Status: Running")
            
            await channel.send(embed=embed)
            print(f"✅ Startup message sent to channel {CHANNEL_ID}")

        except discord.NotFound:
            print(f"❌ ERROR: Channel ID {CHANNEL_ID} not found. Check the ID.")
        except discord.Forbidden:
            print(f"❌ ERROR: Bot does not have permission to send messages in {CHANNEL_ID}.")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

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
