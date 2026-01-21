import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True  # සාමාජිකයන් එන යන එක බලාගන්න මේක ඕනේ
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')

# --- Welcome Event ---
@bot.event
async def on_member_join(member):
    # 1. Server එකට Image එකක් යැවීම
    channel = bot.get_channel(WELCOME_CH_ID)
    
    # Background image එක load කිරීම (ඔයාගේ background.jpg link එක මෙතනට දෙන්න)
    # දැනට මම sample එකක් දාන්නම්, ඔයාට ඕන එකක් GitHub එකට දාලා ඒ link එක දෙන්න පුළුවන්
    background_url = "https://i.imgur.com/8Yv9X6X.jpg" 
    
    background = Editor(await load_image_async(background_url)).resize((800, 450))
    avatar = Editor(await load_image_async(member.display_avatar.url)).resize((150, 150)).circle_image()
    
    # Avatar එක මැදට ගැනීම
    background.paste(avatar, (325, 100))
    
    # නම සහ විස්තර පෙන්වීම
    font_big = Font.poppins(size=40, variant="bold")
    font_small = Font.poppins(size=25, variant="light")
    
    background.text((400, 280), f"WELCOME", color="white", font=font_big, align="center")
    background.text((400, 330), f"{member.name}", color="yellow", font=font_big, align="center")
    background.text((400, 380), f"You are member #{member.guild.member_count}", color="white", font=font_small, align="center")
    
    file = discord.File(fp=background.image_bytes, filename="welcome.png")
    
    if channel:
        await channel.send(f"Welcome to the server, {member.mention}!", file=file)

    # 2. Private Message (DM) එකක් යැවීම
    try:
        await member.send(f"Hello {member.name}, Welcome to our server! Glad to have you here.")
    except:
        print(f"Couldn't send DM to {member.name}")

# --- Leave Event ---
@bot.event
async def on_member_remove(member):
    # Server එකට Text Message එකක් පමණක් යැවීම
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"Goodbye **{member.name}**! We hope to see you again soon.")

    # Private Message (DM) එකක් යැවීම
    try:
        await member.send(f"Goodbye {member.name}. Sorry to see you leaving the server!")
    except:
        print(f"Couldn't send DM to {member.name}")

bot.run(TOKEN)
