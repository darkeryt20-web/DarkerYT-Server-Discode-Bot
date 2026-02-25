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
        intents.members = True  # CRITICAL for role assignment and join events
        super().__init__(command_prefix="?", intents=intents)
        # Use raw GitHub links for direct image access
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_wqnfxgwqnfxgwqnf.png"
        self.footer_icon = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"

    async def create_welcome_card(self, member: discord.Member):
        """Generates a dynamic image with the member's profile picture and name."""
        try:
            async with aiohttp.ClientSession() as session:
                # Download Background
                async with session.get(self.bg_url) as resp:
                    if resp.status != 200: return None
                    bg_bytes = await resp.read()
                
                # Download Avatar
                avatar_url = member.display_avatar.url
                async with session.get(avatar_url) as resp:
                    if resp.status != 200: return None
                    avatar_bytes = await resp.read()

            # Process Background
            background = Image.open(BytesIO(bg_bytes)).convert("RGBA")
            background = background.resize((1024, 500)) 
            
            # Process Avatar (Circular)
            avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
            size = (250, 250)
            avatar = ImageOps.fit(avatar, size, centering=(0.5, 0.5))
            
            mask = Image.new('L', size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0) + size, fill=255)
            avatar.putalpha(mask)

            # Paste Avatar in Center
            bg_width, bg_height = background.size
            av_width, av_height = avatar.size
            offset = ((bg_width - av_width) // 2, (bg_height - av_height) // 2 - 40)
            background.paste(avatar, offset, avatar)

            # Draw Bold Text
            draw = ImageDraw.Draw(background)
            # Defaulting to basic font if system bold is missing
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            except:
                font = ImageFont.load_default()

            name_text = f"{member.name}"
            bbox = draw.textbbox((0, 0), name_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_pos = ((bg_width - text_width) // 2, offset[1] + av_height + 20)
            
            # Text Shadow & Cyan Color
            draw.text((text_pos[0]+3, text_pos[1]+3), name_text, font=font, fill=(0, 0, 0))
            draw.text(text_pos, name_text, font=font, fill=(0, 255, 255))

            final_buffer = BytesIO()
            background.save(final_buffer, format="PNG")
            final_buffer.seek(0)
            return final_buffer
        except Exception as e:
            print(f"Image Error: {e}")
            return None

    async def on_member_join(self, member: discord.Member):
        # 1. --- Role Assignment ---
        ROLE_ID = 1474052348824522854
        role = member.guild.get_role(ROLE_ID)
        if role:
            try:
                await member.add_roles(role)
                print(f"✅ Assigned role to {member.name}")
            except Exception as e:
                print(f"❌ Role Assignment Failed: {e}")

        # 2. --- Send Welcome Message ---
        CHANNEL_ID = 1474041097498923079
        channel = self.get_channel(CHANNEL_ID)
        
        if channel:
            image_data = await self.create_welcome_card(member)
            
            embed = discord.Embed(
                title="Welcome to the Premium Network!",
                description=f"Hello {member.mention}, welcome to **-| SXD VPN |- Premium Network Flash Deals**!\n\nWe provide high-speed, secure connections. Make sure to check our latest flash deals.",
                color=discord.Color.from_str("#2F3136") 
            )
            
            if image_data:
                file = discord.File(fp=image_data, filename="welcome.png")
                embed.set_image(url="attachment://welcome.png")
            else:
                file = None

            embed.set_footer(
                text="Powered By SXD", 
                icon_url=self.footer_icon
            )
            
            await channel.send(content=f"Welcome {member.mention}!", embed=embed, file=file)

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
