import discord
from discord.ext import commands
from datetime import datetime

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1474051484390789253

    @commands.Cog.listener()
    async def on_ready(self):
        # Set a professional Activity status
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="System Integrity"
            ),
            status=discord.Status.online
        )

        # Send the Startup Notification
        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            embed = discord.Embed(
                title="✅ System Operational",
                description="The bot has successfully established a connection.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="Environment", value="Koyeb Cloud", inline=True)
            embed.set_footer(text="Modular System v1.0")
            
            await channel.send(embed=embed)
            print(f"Startup notification sent to {self.log_channel_id}")

async def setup(bot):
    await bot.add_cog(Status(bot))
