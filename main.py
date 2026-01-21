import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import requests
import os

# 1. Intents නිවැරදිව සැකසීම
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} සාර්ථකව Online පැමිණ ඇත!')

@bot.event
async def on_member_join(member):
    # ඔබේ Welcome Channel ID එක මෙහි ලියන්න
    WELCOME_CHANNEL_ID = 123456789012345678 
    
    try:
        # Background රූපය (background.png ගොනුව folder එකේ තිබිය යුතුය)
        background = Image.open("background.jpg").convert("RGBA")
        background = background.resize((900, 500))
        
        # User Avatar එක ලබා ගැනීම
        avatar_url = member.display_avatar.url
        response = requests.get(avatar_url)
        avatar_data = io.BytesIO(response.content)
        avatar_img = Image.open(avatar_data).convert("RGBA")
        
        # Avatar එක රවුම් කිරීම
        size = (200, 200)
        avatar_img = avatar_img.resize(size)
        mask = Image.new('L', size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + size, fill=255)
        output = ImageOps.fit(avatar_img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        
        background.paste(output, (350, 50), output)
        
        # අකුරු ඇඳීම
        draw = ImageDraw.Draw(background)
        try:
            # Arial ෆොන්ට් එක නැත්නම් default එක භාවිතා වේ
            font = ImageFont.truetype("arial.ttf", 50)
        except:
            font = ImageFont.load_default()

        welcome_msg = f"Welcome, {member.name}!"
        w = draw.textlength(welcome_msg, font=font)
        draw.text(((900 - w) / 2, 280), welcome_msg, fill="white", font=font)

        # Image එක Discord එකට යැවිය හැකි ආකාරයට සකස් කිරීම
        with io.BytesIO() as image_binary:
            background.save(image_binary, 'JPG')
            image_binary.seek(0)
            
            # Server එකට යැවීම
            channel = bot.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                file = discord.File(fp=image_binary, filename='background.jpg')
                await channel.send(f"Welcome to our server {member.mention}!", file=file)
            
            # සාමාජිකයාට Private Message (DM) එකක් යැවීම
            try:
                image_binary.seek(0)
                dm_file = discord.File(fp=image_binary, filename='background.jpg')
                await member.send(f"Welcome {member.name}! Glad you joined us.", file=dm_file)
            except Exception as e:
                print(f"DM යැවීමට නොහැකි විය: {e}")

    except Exception as e:
        print(f"Image creation error: {e}")

# වැදගත්: 'YOUR_TOKEN_HERE' වෙනුවට ඔබේ සැබෑ Token එක ඇතුළත් කරන්න
bot.run('MY_BOT_TOKEN')


