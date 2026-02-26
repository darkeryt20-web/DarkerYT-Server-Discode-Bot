import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta

# --- Global Data for Dashboard ---
# මේ දත්ත web.py එකට share වෙනවා
bot_stats = {
    "status": "Offline",
    "servers": 0,
    "members": 0,
    "latency": "0ms",
    "uptime": "0",
    "last_update": ""
}

bot_instance = None # Web server එකට bot පාලනය කරන්න මේක පාවිච්චි කරනවා

class HighPerformanceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None 
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
        global bot_instance
        bot_instance = self # Bot object එක save කරගන්නවා

        print(f'🚀 {self.user} is online and synchronized.')
        
        # Dashboard stats update
        bot_stats["status"] = "Online"
        bot_stats["servers"] = len(self.guilds)
        bot_stats["members"] = sum(g.member_count for g in self.guilds)
        bot_stats["latency"] = f"{round(self.latency * 1000)}ms"
        bot_stats["last_update"] = datetime.now().strftime("%H:%M:%S")

        channel_id = 1474051484390789253
        channel = self.get_channel(channel_id)
        
        if channel:
            adjusted_now = datetime.now() + timedelta(hours=4, minutes=30)
            current_time = adjusted_now.strftime("%I:%M %p")
            current_date = adjusted_now.strftime("%Y-%m-%d")
            
            embed = discord.Embed(
                title="🟢 System Status: Online",
                description="The high-performance core has been initialized successfully.",
                color=discord.Color.from_rgb(46, 204, 113),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="📅 Start Date", value=f"`{current_date}`", inline=True)
            embed.add_field(name="⏰ Adjusted Time", value=f"`{current_time}`", inline=True)
            embed.add_field(name="📡 Latency", value=f"`{bot_stats['latency']}`", inline=True)
            
            image_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_312ul4312ul4312u.png"
            embed.set_image(url=image_url)
            embed.set_thumbnail(url=self.user.display_avatar.url)
            embed.set_footer(text="Powered By SXD • High Performance Mode", icon_url=self.user.display_avatar.url)
            
            await channel.send(embed=embed)

async def start_bot():
    bot = HighPerformanceBot()
    
    async with bot:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            print("❌ CRITICAL: 'DISCORD_TOKEN' not found!")
            return
            
        try:
            await bot.start(token)
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    # සටහන: අපි web.py එක වෙනම රන් කරන නිසා මෙතන threading අවශ්‍ය නැහැ.
    # Dockerfile එකෙන් scripts හතරම එකවර පටන් ගනීවි.
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🤖 Bot is shutting down...")
