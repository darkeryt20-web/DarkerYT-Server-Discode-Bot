import discord
from discord.ext import commands
import time

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # level පණිවිඩ යවන්න ඕන විශේෂ channel එකේ ID එක
        self.LEVEL_LOG_CH_ID = 1463876659320062086
        
        # User data store කරන තැන: {user_id: {"messages": 0, "voice_start": None, "total_voice_mins": 0, "level": 0}}
        self.users = {}

    def get_user_data(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = {"xp": 0, "messages": 0, "voice_start": None, "total_voice_mins": 0, "level": 0}
        return self.users[user_id]

    def check_level_up(self, user_id):
        data = self.get_user_data(user_id)
        current_level = data["level"]
        messages = data["messages"]
        voice_mins = data["total_voice_mins"]
        new_level = current_level

        # --- Level Logic ---
        if current_level == 0 and messages >= 5:
            new_level = 1
        elif current_level == 1 and messages >= 25 and voice_mins >= 5: # Level 2 වෙන්න 5min voice ඉන්න ඕන
            new_level = 2
        elif current_level == 2 and messages >= 50:
            new_level = 3
        elif current_level == 3 and messages >= 100:
            new_level = 4
        elif current_level == 4 and messages >= 200:
            new_level = 5

        if new_level > current_level:
            self.users[user_id]["level"] = new_level
            return new_level
        return None

    async def announce_level_up(self, member, level, current_channel=None):
        """සියලුම තැන්වලට level up පණිවිඩය යවන Function එක"""
        
        embed = discord.Embed(
            title="🎊 LEVEL UP! 🎊",
            description=f"සුභ පැතුම් {member.mention}! ඔයා දැන් **Level {level}** ට Upgrade වුණා! 🚀",
            color=0x00ff00
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="New Rank", value=f"⭐ Level {level}")

        # 1. පණිවිඩය එවපු Channel එකට යැවීම
        if current_channel:
            await current_channel.send(embed=embed)

        # 2. ඔයා දුන්න Specific Channel එකට යැවීම (1463876659320062086)
        log_channel = self.bot.get_channel(self.LEVEL_LOG_CH_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📈 Member Level Up Log",
                description=f"**{member.name}** just reached **Level {level}**!",
                color=0x3498db
            )
            await log_channel.send(embed=log_embed)

        # 3. Private Message (DM) එකක් යැවීම
        try:
            dm_embed = discord.Embed(
                title="🎉 Congratulations!",
                description=f"ඔයා {member.guild.name} server එකේ **Level {level}** ට ආවා. දිගටම chat කරන්න!",
                color=0xe74c3c
            )
            await member.send(embed=dm_embed)
        except:
            # සාමාජිකයාගේ DM OFF කරලා තියෙනවා නම් Error එකක් නොවී skip කරන්න
            print(f"⚠️ Could not send DM to {member.name}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        self.get_user_data(user_id) # data initialize කරනවා
        
        self.users[user_id]["messages"] += 1
        
        lvl = self.check_level_up(user_id)
        if lvl:
            await self.announce_level_up(message.author, lvl, message.channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = member.id
        self.get_user_data(user_id)

        # Voice channel එකට join වීම
        if before.channel is None and after.channel is not None:
            self.users[user_id]["voice_start"] = time.time()

        # Voice channel එකෙන් ඉවත් වීම
        elif before.channel is not None and after.channel is None:
            start_time = self.users[user_id].get("voice_start")
            if start_time:
                duration = (time.time() - start_time) / 60
                self.users[user_id]["total_voice_mins"] += duration
                self.users[user_id]["voice_start"] = None
                
                lvl = self.check_level_up(user_id)
                if lvl:
                    await self.announce_level_up(member, lvl)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Server Boost එකක් කළොත් Level එකක් වැඩි කිරීම
        if not before.premium_since and after.premium_since:
            user_id = after.id
            self.get_user_data(user_id)
            self.users[user_id]["level"] += 1
            await self.announce_level_up(after, self.users[user_id]["level"])

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = self.get_user_data(member.id)
        
        embed = discord.Embed(title=f"📊 {member.name}'s Progress", color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Current Level", value=f"⭐ {data['level']}", inline=True)
        embed.add_field(name="Total Messages", value=f"💬 {data['messages']}", inline=True)
        embed.add_field(name="Voice Time", value=f"🎙️ {round(data['total_voice_mins'], 1)} mins", inline=True)
        embed.set_footer(text="Keep chatting to level up!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
