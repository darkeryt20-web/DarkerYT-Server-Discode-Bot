import discord
import os
from discord.ext import commands

# Bot ට අවශ්‍ය Permissions (Intents) සැකසීම
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello there! I am online.')

# Koyeb එකේදී Environment Variable එකක් විදිහට දෙන TOKEN එක ලබා ගැනීම
token = os.getenv('DISCORD_TOKEN')
bot.run('MY_TOKEN')
