import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')

async def create_welcome_card(member):
    # 1. Background Image එක load කිරීම
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
    background = Editor(await load_image_async(bg_url)).resize((800, 450))
    
    # 2. Avatar එක සහ Decoration (රවුම) සැකසීම
    avatar_img = await load_image_async(member.display_avatar.url)
    avatar = Editor(avatar_img).resize((180, 180)).circle_image()
    
    # මැදට රවුම් border එකක් (Decoration)
    background.canvas.ellipse((305, 85, 495, 275), outline="white", width=5)
    
    # Avatar එක මැදට paste කිරීම
    background.paste(avatar, (310, 90))
    
    # 3. Fonts සැකසීම
    try:
        font_name = Font.poppins(size=50, variant="bold")
        font_sub = Font.poppins(size=30, variant="light")
    except:
        font_name = None # Default
        font_sub = None

    # 4. නම සහ විස්තර අකුරු මැදට (Center) ඇඩ් කිරීම
    background.text((400, 300), f"{member.name}", color="#ffffff", font=font_name, align="center")
    background.text((400, 360), f"WELCOME TO THE SERVER", color="#ffcc00", font=font_sub, align="center")
    background.text((400, 400), f"Member #{member.guild.member_count}", color="#aaaaaa", font=font_sub, align="center")
    
    return discord.File(fp=background.image_bytes, filename="welcome.png")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    
    # Image එක සාදා ගැනීම
    welcome_file = await create_welcome_card(member)
    
    # 1. Server එකට Card Message (Embed) සහ Image එක යැවීම
    if channel:
        embed = discord.Embed(
            title="✨ New Member Joined!",
            description=f"Welcome {member.mention} to **{member.guild.name}**! We are so happy to have you here.",
            color=0x2f3136
        )
        embed.set_image(url="attachment://welcome.png")
        await channel.send(file=welcome_file, embed=embed)

    # 2. Private Message (DM) එකට Card Message සහ Image යැවීම
    try:
        # DM එක සඳහා අලුත් file object එකක් ඕනේ
        dm_file = await create_welcome_card(member)
        dm_embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=f"Hi {member.name}, check out this cool welcome card we made for you! Enjoy your stay.",
            color=discord.Color.blue()
        )
        dm_embed.set_image(url="attachment://welcome.png")
        await member.send(file=dm_file, embed=dm_embed)
    except discord.Forbidden:
        print(f"❌ Could not send DM to {member.name}")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CH_ID)
    
    # Goodbye එකට Text Card (Embed) එකක් පමණක්
    if channel:
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"Goodbye **{member.name}**! We hope to see you again soon.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

    # Private Message (DM) Goodbye
    try:
        await member.send(f"Goodbye {member.name}. You left **{member.guild.name}**. Hope to see you back some day!")
    except:
        pass

bot.run(TOKEN)
