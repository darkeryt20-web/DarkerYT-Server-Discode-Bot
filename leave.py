import discord
from discord.ext import commands

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1463584100966465596
        self.OWNER_ID = 1391883050035581148

    @commands.command(name="leave")
    async def test_leave(self, ctx):
        if ctx.author.id != self.OWNER_ID:
            return

        embed = discord.Embed(
            title="Leave Message Preview",
            description=f"**{ctx.author.name}** has left the server. (Sample)",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=20) # Only visible for 20 seconds

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="Member Left", description=f"**{member.name}** has left the server.", color=discord.Color.red())
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leave(bot))
