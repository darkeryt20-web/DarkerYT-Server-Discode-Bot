import discord
from discord.ext import commands

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.COMMAND_CH_ID = 1463878264522014915

    @commands.command(name="rank")
    async def rank(self, ctx):
        # Check if the command is used in the correct channel
        if ctx.channel.id != self.COMMAND_CH_ID:
            return await ctx.send(f"❌ Please use the <#{self.COMMAND_CH_ID}> channel for commands.")
        
        # Success Message
        await ctx.send(f"📊 {ctx.author.mention}, your rank is currently being calculated!")

async def setup(bot):
    await bot.add_cog(Level(bot))
