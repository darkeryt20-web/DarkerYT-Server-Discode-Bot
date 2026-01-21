import discord
from discord.ext import commands
import os

TOKEN = os.getenv('DISCORD_TOKEN')

# මේක තමයි වැදගත්ම කොටස - intents ඔක්කොම ON කරන්න
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} is online and ready!')

@bot.event
async def on_member_join(member):
    print(f"DEBUG: Member Joined -> {member.name}")
    channel = bot.get_channel(WELCOME_CH_ID)
    if channel:
        try:
            await channel.send(f"Welcome {member.mention} to the server! ❤️")
            print("DEBUG: Message sent successfully!")
        except Exception as e:
            print(f"DEBUG: Error sending message: {e}")
    else:
        print("DEBUG: Welcome channel not found!")

@bot.event
async def on_member_remove(member):
    print(f"DEBUG: Member Left -> {member.name}")
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"Goodbye {member.name}! 👋")

bot.run(TOKEN)
