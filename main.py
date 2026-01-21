import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import requests

# 1. Setup Intents (Fixes your Warning)
intents = discord.Intents.default()
intents.members = True          # To detect new members joining
intents.message_content = True  # To read commands (fixes the warning you saw)

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'---')
    print(f'Bot is Online: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print(f'---')

@bot.event
async def on_member_join(member):
    # --- CONFIGURATION ---
    # Replace with your actual Welcome Channel ID
    WELCOME_CHANNEL_ID = 123456789012345678 
    # Use a backup font if arial isn't found
    font_path = "arial.ttf" 
    
    # 2. Create the Custom Image Card
    try:
        # Load and resize background
        background = Image.open("background.png").convert("RGBA")
        background = background.resize((900, 500))
        
        # Fetch User Avatar
        avatar_url = member.display_avatar.url
        response = requests.get(avatar_url)
        avatar_data = io.BytesIO(response.content)
        avatar_img = Image.open(avatar_data).convert("RGBA")
        
        # Create Circular Avatar with Decoration (Border)
        size = (200, 200)
        avatar_img = avatar_img.resize(size)
        
        mask = Image.new('L', size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + size, fill=255)
        
        # Create a white border/decoration circle
        output = ImageOps.fit(avatar_img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        
        # Paste Avatar onto Background (Centered)
        background.paste(output, (350, 50), output)
        
        # Draw Text (Username)
        draw = ImageDraw.Draw(background)
        try:
            name_font = ImageFont.truetype(font_path, 50)
            sub_font = ImageFont.truetype(font_path, 30)
        except:
            name_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        username_text = f"{member.name}"
        welcome_text = "WELCOME TO THE SERVER"
        
        # Calculate text positions to center them
        name_width = draw.textlength(username_text, font=name_font)
        welcome_width = draw.textlength(welcome_text, font=sub_font)
        
        draw.text(((900 - name_width) / 2, 280), username_text, fill="white", font=name_font)
        draw.text(((900 - welcome_width) / 2, 350), welcome_text, fill="#f0f0f0", font=sub_font)

        # 3. Save to Buffer
        with io.BytesIO() as image_binary:
            background.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            # 4. Send to Server Channel
            channel = bot.get_channel(WELCOME_CHANNEL_ID)
            if channel:
                discord_file = discord.File(fp=image_binary, filename='welcome.png')
                await channel.send(f"Welcome to the family, {member.mention}!", file=discord_file)
            
            # 5. Send Private Message (DM)
            try:
                image_binary.seek(0) # Reset buffer for second use
                dm_file = discord.File(fp=image_binary, filename='welcome.png')
                await member.send(
                    f"Hello {member.name}! Thanks for joining our server. "
                    f"Please read the rules and enjoy your stay!", 
                    file=dm_file
                )
            except discord.Forbidden:
                print(f"Could not DM {member.name} because their DMs are locked.")

    except Exception as e:
        print(f"An error occurred while creating the image: {e}")

# Replace with your token
bot.run('MY_BOT_TOKEN')
