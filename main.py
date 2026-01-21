import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os

TOKEN = os.getenv('DISCORD_TOKEN')

# 100% ක්ම intents වැඩ කරන්න මේක ඕනේ
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'✅ Bot is online as {bot.user}')

@bot.event
async def on_member_join(member):
    print(f"DEBUG: {member.name} joined! Trying to send message...")
    channel = bot.get_channel(WELCOME_CH_ID)
    
    if not channel:
        print(f"❌ Error: Welcome Channel (ID: {WELCOME_CH_ID}) not found!")
        return

    try:
        # Background එක load කිරීම (පොඩි image එකක් ගන්න)
        bg_url = "https://i.imgur.com/8Yv9X6X.jpg" 
        background = Editor(await load_image_async(bg_url)).resize((800, 450))
        
        # Avatar එක load කිරීම
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((150, 150)).circle_image()
        background.paste(avatar, (325, 100))
        
        # Font එක load නොවී crash වෙන එක නතර කරන්න try එකක් දාමු
        try:
            font_big = Font.poppins(size=45, variant="bold")
        except:
            font_big = None # Default font එක ගනී

        background.text((400, 280), "WELCOME", color="white", font=font_big, align="center")
        background.text((400, 335), f"{member.name}", color="#ffcc00", font=font_big, align="center")
        
        file = discord.File(fp=background.image_bytes, filename="welcome.png")
        
        # Server එකට Image එක යැවීම
        await channel.send(content=f"Welcome {member.mention}! ❤️", file=file)
        
        # Private Message (DM) එක යැවීම
        try:
            await member.send(f"Welcome to the server, {member.name}!")
        except:
            print(f"⚠️ Could not send DM to {member.name}")

    except Exception as e:
        print(f"❌ Welcome Logic Error: {e}")
        # Image එක වැඩ කළේ නැතත් අඩුම තරමේ text එක හරි යවන්න:
        await channel.send(f"Welcome to the server, {member.mention}! (Image processing failed)")

@bot.event
async def on_member_remove(member):
    print(f"DEBUG: {member.name} left!")
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"Goodbye **{member.name}**! 👋")

bot.run(TOKEN)



