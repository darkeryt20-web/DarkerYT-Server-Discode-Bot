import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os
from github import Github
from datetime import datetime
import pytz

# --- Configuration ---
TOKEN = os.getenv('DISCORD_TOKEN')
GH_TOKEN = os.getenv('GH_TOKEN')
REPO_NAME = "darkeryt20-web/DarkerYT-Server-Discode-Bot"

# Channel IDs (ඔයාගේ Server එකේ හැටියට මේවා නිවැරදිද බලන්න)
WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# --- GitHub Web Update Function ---
def update_github_web(member_name, avatar_url):
    try:
        g = Github(GH_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file = repo.get_contents("index.html")
        content = file.decoded_content.decode("utf-8")

        # ශ්‍රී ලංකාවේ වෙලාව ලබා ගැනීම
        sl_tz = pytz.timezone('Asia/Colombo')
        join_time = datetime.now(sl_tz).strftime('%Y-%m-%d | %I:%M %p')

        # අලුත් Member පේළිය HTML එකට එකතු කිරීම
        new_entry = f"<tr><td><img src='{avatar_url}'><b>{member_name}</b></td><td class='time'>{join_time}</td></tr>\n"

        if "" in content:
            updated_content = content.replace("", f"\n{new_entry}")
            repo.update_file(file.path, f"Joined: {member_name}", updated_content, file.sha)
            print(f"✅ GitHub Web Updated for {member_name}")
    except Exception as e:
        print(f"❌ GitHub Update Error: {e}")

# --- Welcome Card Generator ---
async def create_welcome_card(member):
    # Background Image (ඔයා දුන්න URL එක)
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
    background = Editor(await load_image_async(bg_url)).resize((800, 450))
    
    # Avatar සැකසීම
    avatar_img = await load_image_async(member.display_avatar.url)
    avatar = Editor(avatar_img).resize((180, 180)).circle_image()
    
    # Avatar Border එක (Decoration)
    background.ellipse(position=(310, 90), width=180, height=180, outline="white", stroke_width=5)
    background.paste(avatar, (310, 90))
    
    # Fonts
    try:
        font_name = Font.poppins(size=50, variant="bold")
        font_sub = Font.poppins(size=30, variant="light")
    except:
        font_name = None 
        font_sub = None

    # Text ඇතුළත් කිරීම
    background.text((400, 300), f"{member.name}", color="#ffffff", font=font_name, align="center")
    background.text((400, 360), "WELCOME TO THE SERVER", color="#ffcc00", font=font_sub, align="center")
    
    return discord.File(fp=background.image_bytes, filename="welcome.png")

# --- Events ---

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')

@bot.event
async def on_member_join(member):
    print(f"DEBUG: {member.name} join වුණා.")
    
    # 1. GitHub Web Update
    update_github_web(member.name, member.display_avatar.url)

    # 2. Welcome Image & Embed
    channel = bot.get_channel(WELCOME_CH_ID)
    try:
        # Server එකට යැවීම
        if channel:
            welcome_file = await create_welcome_card(member)
            embed = discord.Embed(title="✨ New Member!", description=f"Welcome {member.mention}!", color=0x7289da)
            embed.set_image(url="attachment://welcome.png")
            await channel.send(file=welcome_file, embed=embed)

        # Private Message (DM) යැවීම
        try:
            dm_file = await create_welcome_card(member)
            dm_embed = discord.Embed(title=f"Welcome to {member.guild.name}", description=f"Hi {member.name}, enjoy your stay!", color=0x7289da)
            dm_embed.set_image(url="attachment://welcome.png")
            await member.send(file=dm_file, embed=dm_embed)
        except:
            print(f"⚠️ {member.name} ට DM යවන්න බැරි වුණා.")

    except Exception as e:
        print(f"❌ Welcome Logic Error: {e}")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"👋 **{member.name}** left the server.")

bot.run(TOKEN)
