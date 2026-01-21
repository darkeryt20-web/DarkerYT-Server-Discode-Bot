import discord
import os
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # ඔයා ලබාදුන් Channel ID එක මෙතනට දැම්මා
    channel_id = 1463499215954247711 
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("Bot එක දැන් Koyeb හරහා Online ආවා! 🚀")
    else:
        print("Channel එක හොයාගන්න බැරි වුණා. ID එක හරිද කියලා බලන්න.")

@bot.command()
async def hello(ctx):
    await ctx.send('Hello there! I am online.')

# Koyeb Environment Variable එකෙන් Token එක ලබා ගැනීම
token = os.getenv('DISCORD_TOKEN')

if token:
    bot.run(token)
else:
    print("Error: DISCORD_TOKEN කියන Environment Variable එක Koyeb වල දාලා නැහැ!")
