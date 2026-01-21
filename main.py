import os
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageOps, ImageFont
import io
import requests

# Bot intents set kirima (Members wa dakinna meka oni)
intents = discord.Intents.default()
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL_ID = 1463499215954247711 # Oya dunna Channel ID eka

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} online inne!')

@bot.event
async def on_member_join(member):
    # 1. Background image eka load karaganna
    try:
        background = Image.open("background.jpg").convert("RGBA")
    except FileNotFoundError:
        print("Error: 'background.jpg' file eka hoyaganna baha.")
        return

    # 2. Userge profile picture eka download karaganna
    pfp_url = member.avatar.url if member.avatar else member.default_avatar.url
    response = requests.get(pfp_url)
    pfp_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
    
    # 3. Profile picture eka circle ekak karanna
    size = (200, 200) # Circle eke size eka
    pfp_img = pfp_img.resize(size, Image.LANCZOS)
    
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    output_pfp = ImageOps.fit(pfp_img, mask.size, centering=(0.5, 0.5))
    output_pfp.putalpha(mask)

    # 4. Background eke medata profile picture eka paste kirima
    bg_w, bg_h = background.size
    offset = ((bg_w - size[0]) // 2, (bg_h - size[1]) // 2 - 50) # Medata ganna calculations
    background.paste(output_pfp, offset, output_pfp)

    # 5. Userge nama add kirima
    draw = ImageDraw.Draw(background)
    # Font ekak thiyenwa nam path eka danna, nathnam default ekak use wenawa
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    text = f"Welcome, {member.name}!"
    # Text eka medata ganna
    w, h = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (150, 40)
    draw.text(((bg_w - w) // 2, offset[1] + size[1] + 20), text, fill="white", font=font)

    # 6. Image eka save karala channel ekata yawanna
    with io.BytesIO() as image_binary:
        background.save(image_binary, 'PNG')
        image_binary.seek(0)
        
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            # Public message eka (Image eka samaga)
            await channel.send(f"Welcome to the server, {member.mention}!", file=discord.File(fp=image_binary, filename='welcome.png'))
            
            # Private Message (DM) eka
            try:
                await member.send(f"Welcome to our server, {member.name}! Glad to have you here.")
            except discord.Forbidden:
                print(f"User {member.name} ge DM lock karala thiyenne.")

# Me thitheta oyage Bot Token eka danna

bot.run(os.environ.get('MY_BOT_TOKEN'))

