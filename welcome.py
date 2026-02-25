import discord
from discord.ext import commands
from discord import app_commands
from easy_pil import Editor, load_image_async, Font

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1474041097498923079
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/background.jpg"
        self.logo_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"

    async def generate_card(self, member):
        """Image eka generate karana function eka"""
        try:
            background = await load_image_async(self.bg_url)
            editor = Editor(background).resize((800, 450))
            
            avatar = await load_image_async(str(member.display_avatar.url))
            editor.draw_image(avatar, (300, 80), size=(200, 200), circular=True)
            
            font_big = Font.poppins(size=45, variant="bold")
            font_small = Font.poppins(size=25, variant="light")

            editor.text((400, 310), f"WELCOME", color="white", font=font_small, align="center")
            editor.text((400, 360), f"{member.name.upper()}", color="cyan", font=font_big, align="center")
            
            return discord.File(fp=editor.image_bytes, filename="welcome_card.png")
        except Exception as e:
            print(f"Image Error: {e}")
            return None

    # Bot join weddi auto yana message eka
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            file = await self.generate_card(member)
            embed = discord.Embed(
                title="👋 Welcome to 𝙎𝙓𝘿 𝙑𝙋𝙉 - 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙉𝙚𝙩𝙬𝙤𝙧𝙠 𝙁𝙡𝙖𝙨𝙝 𝘿𝙚𝙖𝙡𝙨!",
                description=f"Welcome {member.mention}, Enjoy your stay!",
                color=0x00ffff
            )
            if file: embed.set_image(url="attachment://welcome_card.png")
            embed.set_footer(text="Powered By 𝙎𝙓𝘿", icon_url=self.logo_url)
            await channel.send(file=file, embed=embed)

    # Oya illapu /welcome [user] command eka
    @app_commands.command(name="welcome", description="Create a welcome image for a player")
    @app_commands.describe(member="Select the member to welcome")
    async def welcome_command(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer() # Image eka generate wenna welawa dena nisa
        
        file = await self.generate_card(member)
        embed = discord.Embed(
            title="👋 Player Welcome",
            description=f"Welcome {member.mention} to the server!",
            color=0x00ffff
        )
        if file: embed.set_image(url="attachment://welcome_card.png")
        embed.set_footer(text="Powered By 𝙎𝙓𝘿", icon_url=self.logo_url)
        
        await interaction.followup.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
