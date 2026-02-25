import discord
from discord.ext import commands
from discord import app_commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1474041097498923079
        self.logo_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"

    # Auto welcome message when someone joins
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            embed = discord.Embed(
                title="👋 Welcome to 𝙎𝙓𝘿 𝙑𝙋𝙉!",
                description=f"Hello {member.mention},\nWelcome to **𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙉𝙚𝙩𝙬𝙤𝙧𝙠 𝙁𝙡𝙖𝙨𝙝 𝘿𝙚𝙖𝙡𝙨**!\n\n📌 Please read the rules and enjoy your stay!",
                color=0x00ffff
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Powered By 𝙎𝙓𝘿", icon_url=self.logo_url)
            await channel.send(content=f"Welcome {member.mention}!", embed=embed)

    # /welcome [user] command
    @app_commands.command(name="welcome", description="Send a welcome message to a member")
    @app_commands.describe(member="The member you want to welcome")
    async def welcome_command(self, interaction: discord.Interaction, member: discord.Member):
        # Direct response to stop "Thinking..."
        embed = discord.Embed(
            title="👋 SXD Official Welcome",
            description=f"Welcome {member.mention} to our premium network!",
            color=0x00ffff
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Powered By 𝙎𝙓𝘿", icon_url=self.logo_url)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
