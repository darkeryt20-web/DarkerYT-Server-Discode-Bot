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
        intents.members = True  # Required to see role changes
        super().__init__(command_prefix="?", intents=intents)
        # Using RAW github links for direct image access
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_wqnfxgwqnfxgwqnf.png"
        self.footer_icon = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"
        self.TARGET_ROLE_ID = 1474052348824522854
        self.WELCOME_CHANNEL_ID = 1474041097498923079

    async def create_welcome_card(self, member: discord.Member):
        """Generates the big image with profile picture and bold name."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.bg_url) as resp:
                    bg_bytes = await resp.read()
                async with session.get(member.display_avatar.url) as resp:
                    avatar_bytes = await resp.read()
            except Exception as e:
                print(f"Error downloading images: {e}")
                return None

        # Process Background
        background = Image.open(BytesIO(bg_bytes)).convert("RGBA")
        background = background.resize((1024, 500))
        
        # Process Circular Avatar
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        size = (220, 220)
        avatar = ImageOps.fit(avatar, size, centering=(0.5, 0.5))
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
        avatar.putalpha(mask)

        # Paste Avatar in Center
        bg_w, bg_h = background.size
        av_w, av_h = avatar.size
        offset = ((bg_w - av_w) // 2, (bg_h - av_h) // 2 - 50)
        background.paste(avatar, offset, avatar)

        # Draw Bold Name Text
        draw = ImageDraw.Draw(background)
        try:
            # Standard bold font path for Linux/Docker
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except:
            font = ImageFont.load_default()

        name_text = member.name.upper()
        bbox = draw.textbbox((0, 0), name_text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((bg_w - tw) // 2, offset[1] + av_h + 20), name_text, font=font, fill="#00FFFF")

        final_buffer = BytesIO()
        background.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        return final_buffer

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Triggers only when the user receives the specific Member role ID."""
        # Check if the target role was added in this update
        role_added = any(role.id == self.TARGET_ROLE_ID for role in after.roles) and \
                     not any(role.id == self.TARGET_ROLE_ID for role in before.roles)

        if role_added:
            channel = self.get_channel(self.WELCOME_CHANNEL_ID)
            if not channel:
                return

            print(f"🌟 Role recognized for {after.name}. Generating welcome message...")
            
            image_data = await self.create_welcome_card(after)
            file = discord.File(fp=image_data, filename="welcome.png") if image_data else None

            embed = discord.Embed(
                title="Welcome to the Premium Network!",
                description=f"Hello {after.mention}, welcome to **-| SXD VPN |- Premium Network Flash Deals**!\nWe provide high-speed, secure connections. Make sure to check our latest flash deals.",
                color=discord.Color.from_str("#2F3136") # Sleek Dark Mode
            )
            
            if file:
                embed.set_image(url="attachment://welcome.png")
            
            embed.set_footer(
                text="Powered By SXD", 
                icon_url=self.footer_icon
            )

            await channel.send(content=f"Welcome {after.mention}!", embed=embed, file=file)

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
