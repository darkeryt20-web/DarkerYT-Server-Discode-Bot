import discord
from discord.ext import commands
import os

# Koyeb Environment Variable එකෙන් Token එක ගන්නවා
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    if channel:
        await channel.send(f"Welcome {member.mention}! ❤️")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"Goodbye {member.name}! 👋")

# මෙතන TOKEN කියන එක variable එකක් විදිහට දෙන්න (Quotes නැතුව)
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token Error: Please check Koyeb Environment Variables!")
