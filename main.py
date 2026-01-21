import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageOps, ImageFont
import io
import requests
import os
import subprocess
import sys

# 1. Bot intents set kirima
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
WELCOME_CHANNEL_ID = 1463499215954247711 

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} online inne!')

# --- 2. UPDATE COMMAND (GitHub eken aran auto restart wenna) ---
@bot.command()
async def update(ctx):
    # Kaata hari restart karanna oni nam me command eka gahanna puluwan
    msg = await ctx.send("🔄 GitHub එකෙන් අලුත් Code එක ගන්නවා...")
    try:
        output = subprocess.check_output(['git', 'pull']).decode("utf-8")
        await msg.edit(content=f"✅ Code Updated:\n```{output}```\nRestarting...")
        # VPS eke restart wenna
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        await msg.edit(content=f"❌ Error: {e}")

# --- 3. WELCOME IMAGE FIXES ---
@bot.event
async def on_member_join(member):
    try:
        # Background image eka load karaganna
        background = Image.open("background.jpg").convert("RGBA")
        bg_w, bg_h = background.size

        # Userge profile picture eka download karaganna
        pfp_url = member.avatar.url if member.avatar else member.default_avatar.url
        response = requests.get(pfp_url)
        pfp_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        
        # Profile picture eka resize karala circle ekak karanna
        size = (200, 200)
        pfp_img = pfp_img.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + size, fill=255)
        
        output_pfp = ImageOps.fit(pfp_img, mask.size, centering=(0.5, 0.5))
        output_pfp.putalpha(mask)

        # Background eke hariyatama medata paste kirima
        offset = ((bg_w - size[0]) // 2, (bg_h - size[1]) // 2 - 50)
        background.paste(output_pfp, offset, output_pfp)

        # Userge nama add kirima
        draw = ImageDraw.Draw(background)
        try:
            # VPS eke arial nathnam default ekak gannawa
            font = ImageFont.truetype("arial.ttf", 50)
        except:
            font = ImageFont.load_default()

        text = f"{member.name}"
        
        # Text eka medata ganna calculations (Fixed)
        if hasattr(draw, 'textbbox'):
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            w, h = draw.textsize(text, font=font)

        draw.text(((bg_w - w) // 2, offset[1] + size[1] + 30), text, fill="white", font=font)

        # Image eka memory ekata save karala yawanna
        with io.BytesIO() as image_binary:
            background.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            channel = bot.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                await channel.send(f"Welcome to the server, {member.mention}!", file=discord.File(fp=image_binary, filename='welcome.png'))
                
    except Exception as e:
        print(f"Image error: {e}")

# Bot Token eka (Mehema danna, nathnam environment variable eke 'MY_BOT_TOKEN' kiyala danna)
bot.run(os.environ.get('MY_BOT_TOKEN', 'OYAGE_BOT_TOKEN_EKA_METHANATA_DANNA'))
