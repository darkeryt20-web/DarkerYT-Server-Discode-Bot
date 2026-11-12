import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Bot Setup
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Discord Verification Bot is ready!")

async def main():
    if not TOKEN:
        print("Error: DISCORD_TOKEN is missing!")
        return
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
