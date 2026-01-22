import discord
from discord.ext import commands, tasks
import time

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary to store user data: {user_id: {"xp": 0, "messages": 0, "voice_start": None, "total_voice_mins": 0}}
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

        # Level Logic
        if current_level == 0 and messages >= 5:
            new_level = 1
        elif current_level == 1 and messages >= 25 and voice_mins >= 5: # 5 + 20 more = 25 total
            new_level = 2
        elif current_level == 2 and messages >= 50: # Example for Level 3
            new_level = 3
        elif current_level == 3 and messages >= 100: # Example for Level 4
            new_level = 4
        elif current_level == 4 and messages >= 200: # Example for Level 5
            new_level = 5

        if new_level > current_level:
            self.users[user_id]["level"] = new_level
            return new_level
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        data = self.get_user_data(user_id)
        
        # Add message count
        self.users[user_id]["messages"] += 1
        
        # Check Level Up
        lvl = self.check_level_up(user_id)
        if lvl:
            await message.channel.send(f"🎉 පට්ට! {message.author.mention}, ඔයා දැන් **Level {lvl}** ට ආවා!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = member.id
        data = self.get_user_data(user_id)

        # Joined a voice channel
        if before.channel is None and after.channel is not None:
            self.users[user_id]["voice_start"] = time.time()

        # Left a voice channel
        elif before.channel is not None and after.channel is None:
            start_time = self.users[user_id].get("voice_start")
            if start_time:
                duration = (time.time() - start_time) / 60 # Convert to minutes
                self.users[user_id]["total_voice_mins"] += duration
                self.users[user_id]["voice_start"] = None
                
                # Check for level up after leaving voice
                lvl = self.check_level_up(user_id)
                if lvl:
                    try:
                        await member.send(f"🚀 නියමයි! Voice හිටපු නිසා ඔයා **Level {lvl}** ට Upgrade වුණා!")
                    except:
                        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Boost logic
        if not before.premium_since and after.premium_since:
            user_id = after.id
            data = self.get_user_data(user_id)
            # Give instant level or boost XP
            self.users[user_id]["level"] += 1 
            await after.guild.system_channel.send(f"💎 {after.mention} Server එක Boost කරපු නිසා Level එකක් ලැබුණා!")

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = self.get_user_data(member.id)
        embed = discord.Embed(title=f"📊 {member.name}'s Stats", color=discord.Color.green())
        embed.add_field(name="Level", value=data["level"])
        embed.add_field(name="Messages", value=data["messages"])
        embed.add_field(name="Voice Time (Mins)", value=round(data["total_voice_mins"], 1))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
