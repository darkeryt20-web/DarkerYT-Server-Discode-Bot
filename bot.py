import discord
import os
from discord.ext import commands

# Token eka environment variable ekakin ganna (Security walata)
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot commands start karanna oni '!' wage symbol ekakin
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello! I am your Discord bot!')

# Bot eka run karanna
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_TOKEN not found in environment variables.")
