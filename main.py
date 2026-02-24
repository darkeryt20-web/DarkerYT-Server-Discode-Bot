import discord
from discord.ext import commands
import os
import asyncio

# --- Configuration ---
TOKEN = os.getenv('MTQ2MzUxNDE1OTkzNjQ0MjQ2MQ.GySjSf.gY-blUxLJHQmN3fk-iCL0Jne5uqnJ-wHw2AOK4')
LOG_CHANNEL_ID = 1464920331461328958 

# Setup Intents (All intents are required for Leveling/Welcome/Anti-link)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online and ready!')
    
    # Sync Slash Commands for Music and other interactions
    try:
        await bot.tree.sync()
        print("🚀 Slash commands synced successfully.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    # Send Startup Message to Bot Logs Channel
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🤖 Bot Status: Online",
            description=f"**{bot.user.name}** has been successfully started!\nAll extensions are now operational.",
            color=discord.Color.green()
        )
        embed.set_footer(text="System Healthy")
        await channel.send(embed=embed)

async def load_extensions():
    # Adding 'antilink' to the extensions list as requested
    extensions = ["level", "music", "welcome", "leave", "antilink"]
    
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Extension Loaded: {ext}")
        except Exception as e:
            print(f"❌ Error loading {ext}: {e}")

async def main():
    async with bot:
        # Load all cog files before starting the bot
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔴 Bot is shutting down...")

