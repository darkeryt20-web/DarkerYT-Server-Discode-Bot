import discord
from discord.ext import commands
import os
import threading
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
from flask import Flask
from datetime import datetime

# --- Health Check (Port 8002) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Welcomer Bot is Live!", 200

def run_web():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8002)

# --- Bot Logic ---
class WelcomeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # CRITICAL: Must be enabled in Developer Portal
        super().__init__(command_prefix="?", intents=intents)
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_wqnfxgwqnfxgwqnf.png"
        self.footer_icon = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"

    async def create_welcome_card(self, member: discord.Member):
        """Generates a dynamic image with the member's profile picture and name."""
        async with aiohttp.ClientSession() as session:
            # 1. Download Background and Avatar
            async with session.get(self.bg_url) as resp:
                if resp.status != 200: return None
                bg_bytes = await resp.read()
            
            avatar_url = member.display_avatar.url
            async with session.get(avatar_url) as resp:
                if resp.status != 200: return None
                avatar_bytes = await resp.read()

        # 2. Process Background
        background = Image.open(BytesIO(bg_bytes)).convert("RGBA")
        background = background.resize((1024, 500)) # Standardizing size
        
        # 3. Process Avatar (Make it circular)
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        size = (250, 250)
        avatar = ImageOps.fit(avatar, size, centering=(0.5, 0.5))
        
        mask = Image.new('L', size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + size, fill=255)
        
        circular_avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        circular_avatar.putalpha(mask)

        # 4. Composite Avatar onto Background (Center)
        bg_width, bg_height = background.size
        av_width, av_height = circular_avatar.size
        offset = ((bg_width - av_width) // 2, (bg_height - av_height) // 2 - 40)
        background.paste(circular_avatar, offset, circular_avatar)

        # 5. Add Text (Member Name)
        draw = ImageDraw.Draw(background)
        try:
            # Attempt to use a bold system font, default to basic if not found
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()

        name_text = f"{member.name}"
        # Calculate text position to center it below the avatar
        bbox = draw.textbbox((0, 0), name_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_pos = ((bg_width - text_width) // 2, offset[1] + av_height + 20)
        
        # Draw text with a slight shadow for readability
        draw.text((text_pos[0]+2, text_pos[1]+2), name_text, font=font, fill=(0, 0, 0))
        draw.text(text_pos, name_text, font=font, fill=(0, 255, 255)) # Cyan Text

        # 6. Save to Bytes
        final_buffer = BytesIO()
        background.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        return final_buffer

    async def on_member_join(self, member: discord.Member):
        # REPLACE with your Welcome Channel ID
        WELCOME_CHANNEL_ID = 1474076593382096906 
        channel = self.get_channel(WELCOME_CHANNEL_ID)
        
        if not channel:
            print(f"❌ Welcome Channel {WELCOME_CHANNEL_ID} not found.")
            return

        # Generate the Image
        image_data = await self.create_welcome_card(member)
        file = discord.File(fp=image_data, filename=f"welcome_{member.id}.png") if image_data else None

        # Create Embed
        embed = discord.Embed(
            title="Welcome to the Premium Network!",
            description=f"Hello {member.mention}, welcome to **-| SXD VPN |- Premium Network Flash Deals**!\n\nWe provide high-speed, secure connections. Make sure to check our latest flash deals.",
            color=discord.Color.from_str("#00FFFF") # Flashy Cyan
        )
        
        # Set images
        if file:
            embed.set_image(url=f"attachment://welcome_{member.id}.png")
        
        embed.set_footer(
            text="Powered By SXD", 
            icon_url="https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"
        )
        embed.timestamp = datetime.now()

        await channel.send(content=f"Welcome {member.mention}!", embed=embed, file=file)
        print(f"✅ Welcomed {member.name} to the server.")

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    bot = WelcomeBot()
    async with bot:
        token = os.getenv('DISCORD_TOKEN_WELCOME')
        if token:
            await bot.start(token)
        else:
            print("❌ MISSING: DISCORD_TOKEN_WELCOME")

if __name__ == "__main__":
    asyncio.run(main())
