import discord
from discord.ext import commands, tasks
import random
import datetime

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_CH_ID = 1463876659320062086    # Level Up Log Channel
        self.CMD_CH_ID = 1463878264522014915    # .level වැඩ කරන Channel එක
        
        # XP Table (Level: Total XP required for that level)
        self.xp_table = {
            1: 155, 2: 220, 3: 295, 4: 380, 5: 475, 6: 580, 7: 695, 8: 820, 9: 955, 10: 1100,
            11: 1255, 12: 1420, 13: 1595, 14: 1780, 15: 1975, 16: 2180, 17: 2395, 18: 2620, 19: 2855, 20: 3100,
            21: 3355, 22: 3620, 23: 3895, 24: 4180, 25: 4475, 26: 4780, 27: 5095, 28: 5420, 29: 5755, 30: 6100,
            31: 6455, 32: 6820, 33: 7195, 34: 7580, 35: 7975, 36: 8380, 37: 8795, 38: 9220, 39: 9655, 40: 10100,
            41: 10555, 42: 11020, 43: 11495, 44: 11980, 45: 12475, 46: 12980, 47: 13495, 48: 14020, 49: 14555, 50: 268275
        }

        self.users = {}
        self.voice_xp_loop.start()

    def get_user(self, uid):
        if uid not in self.users:
            self.users[uid] = {
                "xp": 0, "level": 0, "last_msg": "", 
                "spam_count": 0, "cooldown": datetime.datetime.min, 
                "blocked_until": datetime.datetime.min
            }
        return self.users[uid]

    async def check_level_up(self, member, current_channel):
        u_data = self.get_user(member.id)
        current_xp = u_data["xp"]
        current_lvl = u_data["level"]
        
        # ඊළඟ level එකට අවශ්‍ය XP තිබේදැයි බැලීම
        next_lvl = current_lvl + 1
        if next_lvl in self.xp_table and current_xp >= self.xp_table[next_lvl]:
            u_data["level"] = next_lvl
            
            embed = discord.Embed(
                title="🎊 LEVEL UP!", 
                description=f"සුභ පැතුම් {member.mention}! ඔයා දැන් **Level {next_lvl}** ට ආවා! 🚀", 
                color=0x00ff00
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            # 1. පණිවිඩය එවූ channel එකට
            if current_channel:
                await current_channel.send(embed=embed)
            
            # 2. Log Channel එකට (ID: 1463876659320062086)
            log_ch = self.bot.get_channel(self.LOG_CH_ID)
            if log_ch:
                await log_ch.send(f"📈 **{member.name}** just reached **Level {next_lvl}**!")
            
            # 3. Private Message (DM)
            try:
                await member.send(f"නියමයි! ඔයා {member.guild.name} server එකේ Level {next_lvl} වුණා!")
            except:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        u_data = self.get_user(message.author.id)
        now = datetime.datetime.now()

        # XP Block වී ඇත්දැයි බැලීම (Anti-spam penalty)
        if now < u_data["blocked_until"]:
            return

        # --- Anti-Spam Logic ---
        if message.content.lower() == u_data["last_msg"].lower() and len(message.content) > 1:
            u_data["spam_count"] += 1
            if u_data["spam_count"] >= 3:
                u_data["blocked_until"] = now + datetime.timedelta(days=1)
                await message.channel.send(f"⚠️ {message.author.mention}, ඔයා එකම පණිවිඩය කිහිපවරක් එවු නිසා ඔයාගේ XP පැය 24කට තහනම් කළා!")
                return
            else:
                await message.channel.send(f"🚫 {message.author.mention}, කරුණාකර spam කරන්න එපා! (Warning {u_data['spam_count']}/3)")
                return
        else:
            u_data["last_msg"] = message.content
            u_data["spam_count"] = 0

        # --- Cooldown (30s) ---
        if now < u_data["cooldown"]:
            return

        # --- Give XP (10-20) ---
        u_data["xp"] += random.randint(10, 20)
        u_data["cooldown"] = now + datetime.timedelta(seconds=30)

        await self.check_level_up(message.author, message.channel)

    @tasks.loop(minutes=1)
    async def voice_xp_loop(self):
        """විනාඩියකට වරක් Voice XP ලබාදීම (Mic On/Off අදාළ නොවේ)"""
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if len(vc.members) < 1: continue # කවුරුත් නැත්නම් skip කරන්න
                
                for member in vc.members:
                    if member.bot: continue
                    
                    u_data = self.get_user(member.id)
                    if datetime.datetime.now() < u_data["blocked_until"]:
                        continue
                    
                    # මයික් එක ඕෆ් වුණත් දැන් XP ලැබෙනවා
                    u_data["xp"] += random.randint(5, 15)
                    
                    # Voice වලදී level up වුණොත් log channel එකට පමණක් දමමු
                    await self.check_level_up(member, None)

    @commands.command(name="level")
    async def level_cmd(self, ctx):
        # Command එක වැඩ කරන්නේ නියමිත channel එකේ පමණි
        if ctx.channel.id != self.CMD_CH_ID:
            return await ctx.send(f"❌ කරුණාකර මේ command එක <#{self.CMD_CH_ID}> channel එකේ පාවිච්චි කරන්න.")

        u_data = self.get_user(ctx.author.id)
        lvl = u_data["level"]
        xp = u_data["xp"]
        
        # ඊළඟ level එකට අවශ්‍ය ප්‍රමාණය සෙවීම
        next_lvl = lvl + 1
        needed = self.xp_table.get(next_lvl, "MAX")
        
        embed = discord.Embed(title=f"📊 {ctx.author.name}'s Level Stats", color=0x3498db)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="Current Level", value=f"⭐ Level {lvl}", inline=True)
        embed.add_field(name="Total XP", value=f"✨ {xp} XP", inline=True)
        embed.add_field(name="Next Level Requirement", value=f"🎯 {needed} XP", inline=False)
        embed.set_footer(text="දිගටම Active වෙලා ඉන්න!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
