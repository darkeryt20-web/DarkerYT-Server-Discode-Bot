import discord
from discord.ext import commands

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.OWNER_ID = 1391883050035581148

    @commands.command(name="level")
    async def check_level(self, ctx):
        if ctx.author.id != self.OWNER_ID:
            return

        # Preview of level system
        embed = discord.Embed(
            title="Level System Preview",
            description=f"User: {ctx.author.mention}\nCurrent Rank: Processing...",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, delete_after=20)

async def setup(bot):
    await bot.add_cog(Level(bot))
