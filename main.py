import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask
from datetime import datetime, timedelta

# --- Health Check Server ---
app = Flask(__name__)

@app.route('/')
def health(): 
    return "Bot is Live!", 200

def run_web(): 
    # Suppress flask logging for a cleaner console
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8000)

# --- Bot Logic ---
class HighPerformanceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None # Optional: Remove default help for custom ones
        )
        self.start_time = datetime.now()

    async def setup_hook(self):
        """Initializes cogs and syncs slash commands."""
        if not os.path.exists('./cogs'): 
            os.makedirs('./cogs')
            
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Loaded Cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
        
        await self.tree.sync()

    async def on_ready(self):
        print(f'🚀 {self.user} is online and synchronized.')
        
        # Replace with your specific channel ID
        channel_id = 1474051484390789253
        channel = self.get_channel(channel_id)
        
        if channel:
            # --- Time Calculation (Adding 4 Hours & 30 Minutes) ---
            # Using timedelta ensures dates roll over correctly if it's near midnight
            adjusted_now = datetime.now() + timedelta(hours=4, minutes=30)
            
            current_time = adjusted_now.strftime("%I:%M %p")
            current_date = adjusted_now.strftime("%Y-%m-%d")
            
            # --- Enhanced Embed ---
            embed = discord.Embed(
                title="🟢 System Status: Online",
                description="The high-performance core has been initialized successfully.",
                color=discord.Color.from_rgb(46, 204, 113), # Nice emerald green
                timestamp=datetime.now() # Real-time footer timestamp
            )
            
            embed.add_field(name="📅 Start Date", value=f"`{current_date}`", inline=True)
            embed.add_field(name="⏰ Adjusted Time", value=f"`{current_time}`", inline=True)
            embed.add_field(name="📡 Latency", value=f"`{round(self.latency * 1000)}ms`", inline=True)
            
            # Using the raw GitHub link provided
            image_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_312ul4312ul4312u.png"
            embed.set_image(url=image_url)
            
            embed.set_thumbnail(url=self.user.display_avatar.url)
            embed.set_footer(text="Powered By SXD • High Performance Mode", icon_url=self.user.display_avatar.url)
            
            await channel.send(embed=embed)

# --- Entry Point ---
async def main():
    # Run the web server in a separate thread to keep the bot alive on hosts like Replit/Render
    threading.Thread(target=run_web, daemon=True).start()
    
    bot = HighPerformanceBot()
    
    async with bot:
        # Check for token in Environment Variables
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ CRITICAL: 'DISCORD_TOKEN' not found in environment variables!")
            return
            
        try:
            await bot.start(token)
        except discord.LoginFailure:
            print("❌ CRITICAL: Invalid Discord Token provided.")
        except Exception as e:
            print(f"❌ AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🤖 Bot is shutting down...")
