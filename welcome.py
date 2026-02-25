import discord
from discord.ext import commands
from discord import app_commands
from easy_pil import Editor, load_image_async, Font
import asyncio

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1474041097498923079
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/background.jpg"
        self.logo_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"

    async def create_welcome_card(self, member):
        """Helper function to generate the image"""
        background = await load_image_async(self.bg_url)
        editor = Editor(background).resize((800, 450))
        
        # Member Avatar
        avatar = await load_image_async(str(member.display_avatar.url))
        editor.draw_image(avatar, (300, 100), size=(200, 200), circular=True)
        
        # Fonts
        font_big = Font.poppins(size=40, variant="bold")
        font_small = Font.poppins(size=25, variant="light")

        editor.text((400, 320), f"WELCOME {member.name.upper()}", color="white", font=font_big, align="center")
        editor.text((400, 370), f"Member #{member.guild.member_count}", color="#aaaaaa", font=font_small, align="center")
        
        return discord.File(fp=editor.image_bytes, filename="welcome.png")

    def create_welcome_embed(self, member):
        """Helper to create the rich embed"""
        embed = discord.Embed(
            title="👋 Welcome to 𝙎𝙓𝘿 𝙑𝙋𝙉 - 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙉𝙚𝙩𝙬𝙤𝙧𝙠 𝙁𝙡𝙖𝙨𝙝 𝘿𝙚𝙖𝙡𝙨!",
            description=f"👋 Hello {member.mention},\n📌 Please read the rules and enjoy your stay!",
            color=0x2f3136
        )
        embed.set_image(url="attachment://welcome.png")
        embed.set_footer(text="Powered By 𝙎𝙓𝘿", icon_url=self.logo_url)
        return embed

    # --- Auto Welcome on Join ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            file = await self.create_welcome_card(member)
            embed = self.create_welcome_embed(member)
            await channel.send(content=f"Welcome {member.mention}!", embed=embed, file=file)

    # --- Slash Commands Group ---
    @app_commands.command(name="welcome", description="Welcome management commands")
    @app_commands.describe(user="Specific player to welcome", mode="Choose 'temporary' or 'all'")
    async def welcome(self, interaction: discord.Interaction, user: discord.Member = None, mode: str = None):
        
        # 1. /welcome [player_name]
        if user and mode is None:
            await interaction.response.defer() # Image hadana nisa defer karanna ona
            file = await self.create_welcome_card(user)
            embed = self.create_welcome_embed(user)
            await interaction.followup.send(embed=embed, file=file)

        # 2. /welcome temporary
        elif mode == "temporary":
            await interaction.response.send_message(f"👋 Welcome to the server! (This message will vanish in 30s)", delete_after=30)

        # 3. /welcome all
        elif mode == "all":
            await interaction.response.send_message("Generating welcome cards for everyone... (This might take a moment)", ephemeral=True)
            for member in interaction.guild.members:
                if not member.bot:
                    file = await self.create_welcome_card(member)
                    embed = self.create_welcome_embed(member)
                    await interaction.channel.send(embed=embed, file=file)
                    await asyncio.sleep(1) # Rate limit wenna nathi wenna 1s rest ekak

async def setup(bot):
    await bot.add_cog(Welcome(bot))
