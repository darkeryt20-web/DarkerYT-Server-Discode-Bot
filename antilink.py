import discord
from discord.ext import commands
import re

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # --- CONFIGURATION ---
        self.LINK_ALLOW_CH = 1463842297853771806  # Link දාන්න පුළුවන් Channel එක
        self.WARN_CHANNEL = 1464965728309477565   # Warning යන්න ඕන Channel එක

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bot messages සහ Allowed Channel එකේ messages මගහරින්න
        if message.author.bot or message.channel.id == self.LINK_ALLOW_CH:
            return

        # Link Regex Pattern (Discord invites, YouTube, HTTP/HTTPS)
        link_pattern = r"(https?://|www\.|discord\.(gg|io|me|li)|youtube\.com|youtu\.be)"
        
        if re.search(link_pattern, message.content):
            try:
                await message.delete() # Message එක මකනවා
                
                # Warning Channel එකට මැසේජ් එක යැවීම
                warn_ch = self.bot.get_channel(self.WARN_CHANNEL)
                if warn_ch:
                    embed = discord.Embed(
                        title="🚫 Unauthorized Link Detected",
                        description=f"{message.author.mention}, links are not allowed in <#{message.channel.id}>.\nPlease use <#{self.LINK_ALLOW_CH}>.",
                        color=discord.Color.red()
                    )
                    await warn_ch.send(content=f"{message.author.mention}", embed=embed)
            except Exception as e:
                print(f"Error in AntiLink: {e}")

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
