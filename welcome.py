import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime
# අපේ පොදු දත්ත ගොනුවෙන් welcome_stats ලබා ගැනීම
from shared_data import welcome_stats

# --- Bot Logic ---
class WelcomeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # සාමාජිකයින් පැමිණීම පරීක්ෂා කිරීමට අත්‍යවශ්‍යයි
        super().__init__(command_prefix="?", intents=intents)
        
        # GitHub RAW links
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Gemini_Generated_Image_wqnfxgwqnfxgwqnf.png"
        self.footer_icon = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"
        self.TARGET_ROLE_ID = 1474052348824522854
        self.WELCOME_CHANNEL_ID = 1474041097498923079

    async def create_welcome_card(self, member: discord.Member):
        """Welcome Image එක සාදන ආකාරය."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.bg_url) as resp:
                    bg_bytes = await resp.read()
                async with session.get(member.display_avatar.url) as resp:
                    avatar_bytes = await resp.read()
            except Exception as e:
                print(f"Error downloading images: {e}")
                return None

        # පින්තූරය සැකසීම
        background = Image.open(BytesIO(bg_bytes)).convert("RGBA")
        background = background.resize((1024, 500))
        
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        size = (220, 220)
        avatar = ImageOps.fit(avatar, size, centering=(0.5, 0.5))
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
        avatar.putalpha(mask)

        bg_w, bg_h = background.size
        av_w, av_h = avatar.size
        offset = ((bg_w - av_w) // 2, (bg_h - av_h) // 2 - 50)
        background.paste(avatar, offset, avatar)

        draw = ImageDraw.Draw(background)
        try:
            # Docker එකේ පාවිච්චි කරන standard font එක
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

    async def on_ready(self):
        # Dashboard එකේ status එක Online ලෙස වෙනස් කිරීම
        welcome_stats["status"] = "Online"
        print(f"🌟 Welcomer Bot: {self.user} is online.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Role එක ලැබුණු විට පමණක් Welcome message එක යවයි."""
        role_added = any(role.id == self.TARGET_ROLE_ID for role in after.roles) and \
                     not any(role.id == self.TARGET_ROLE_ID for role in before.roles)

        if role_added:
            channel = self.get_channel(self.WELCOME_CHANNEL_ID)
            if not channel: return

            print(f"🌟 Role recognized for {after.name}. Generating welcome message...")
            
            image_data = await self.create_welcome_card(after)
            file = discord.File(fp=image_data, filename="welcome.png") if image_data else None

            embed = discord.Embed(
                title="Welcome to the Premium Network!",
                description=f"Hello {after.mention}, welcome to **-| SXD VPN |- Premium Network Flash Deals**!",
                color=discord.Color.from_str("#2F3136")
            )
            
            if file: embed.set_image(url="attachment://welcome.png")
            embed.set_footer(text="Powered By SXD", icon_url=self.footer_icon)

            await channel.send(content=f"Welcome {after.mention}!", embed=embed, file=file)
            
            # Dashboard දත්ත යාවත්කාලීන කිරීම (Update Stats)
            welcome_stats["welcomes_sent"] += 1
            welcome_stats["last_welcome"] = after.name

async def start_welcome_bot():
    bot = WelcomeBot()
    async with bot:
        token = os.getenv('DISCORD_TOKEN_WELCOME') or os.getenv('DISCORD_TOKEN')
        if token:
            await bot.start(token)
        else:
            print("❌ MISSING: Welcome Bot Token")

if __name__ == "__main__":
    try:
        asyncio.run(start_welcome_bot())
    except KeyboardInterrupt:
        print("Welcomer bot shutting down...")
