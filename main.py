import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import requests

# 1. Intents සැකසීම (Warnings ඉවත් කිරීමට)
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'---')
    print(f'Bot එක වැඩ: {bot.user.name}')
    print(f'---')

@bot.event
async def on_member_join(member):
    # --- සැකසුම් ---
    # ඔබේ Welcome Channel ID එක මෙතැනට ලබා දෙන්න
    WELCOME_CHANNEL_ID = 123456789012345678 
    
    try:
        # Background රූපය විවෘත කිරීම
        background = Image.open("background.png").convert("RGBA")
        background = background.resize((900, 500))
        
        # සාමාජිකයාගේ Avatar එක ලබා ගැනීම
        avatar_url = member.display_avatar.url
        response = requests.get(avatar_url)
        avatar_data = io.BytesIO(response.content)
        avatar_img = Image.open(avatar_data).convert("RGBA")
        
        # Avatar එක රවුම් හැඩයට කැපීම
        size = (200, 200)
        avatar_img = avatar_img.resize(size)
        mask = Image.new('L', size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + size, fill=255)
        
        output = ImageOps.fit(avatar_img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        
        # Background එක මත Avatar එක ඇලවීම
        background.paste(output, (350, 50), output)
        
        # අකුරු ලිවීම (Username එක)
        draw = ImageDraw.Draw(background)
        try:
            font = ImageFont.truetype("arial.ttf", 50)
        except:
            font = ImageFont.load_default()

        text = f"Welcome, {member.name}!"
        w = draw.textlength(text, font=font)
        draw.text(((900 - w) / 2, 280), text, fill="white", font=font)

        # රූපය Buffer එකට Save කිරීම
        with io.BytesIO() as image_binary:
            background.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            # 2. Server Channel එකට යැවීම
            channel = bot.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                file = discord.File(fp=image_binary, filename='welcome.png')
                await channel.send(f"Welcome to the server, {member.mention}!", file=file)
            
            # 3. සාමාජිකයාට Direct Message (DM) එකක් යැවීම
            try:
                image_binary.seek(0) 
                dm_file = discord.File(fp=image_binary, filename='welcome.png')
                await member.send(f"ආයුබෝවන් {member.name}, අපේ Server එකට සාදරයෙන් පිළිගන්නවා!", file=dm_file)
            except:
                print(f"{member.name} ගේ DM ලොක් කර ඇත.")

    except Exception as e:
        print(f"Error: {e}")

# ඔබේ Token එක මෙතැනට ලබා දෙන්න
bot.run('ඔබේ_සැබෑ_BOT_TOKEN_එක_මෙහි_යොදන්න')
