import discord
from discord.ext import commands

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1463584100966465596

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Member Left", 
                description=f"**{member.name}** has left the server. We hope to see you again soon! 👋", 
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leave(bot))
