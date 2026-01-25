import discord
from discord.ext import commands
import os
import asyncio

# --- Configuration ---
TOKEN = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL_ID = 1464920331461328958 

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online and ready!')
    try:
        await bot.tree.sync()
        print("🚀 Slash commands synced.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🤖 Bot Status: Online",
            description=f"**{bot.user.name}** has been successfully started!\nAll extensions are operational.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)

async def load_extensions():
    extensions = ["level", "music", "welcome", "leave"]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Extension Loaded: {ext}")
        except Exception as e:
            print(f"❌ Error loading {ext}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
