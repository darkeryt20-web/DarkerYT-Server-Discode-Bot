import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = 1474041097498923079
        self.goodbye_channel_id = 1474041189501243558

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            embed = discord.Embed(
                title="👋 Welcome to the Server!",
                description=f"Welcome {member.mention}! we're glad to have you here.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Account Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.goodbye_channel_id)
        if channel:
            embed = discord.Embed(
                title="😢 Goodbye",
                description=f"{member.display_name} has left the server. We'll miss you!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Current Members: {member.guild.member_count}")
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
