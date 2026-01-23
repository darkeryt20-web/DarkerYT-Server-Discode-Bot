import discord
from discord.ext import commands, tasks
import random
import datetime

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_CH_ID = 1463876659320062086    # Level Up පණිවිඩ යන Channel එක
        self.CMD_CH_ID = 1463878264522014915    # Leaderboards වැඩ කරන Channel එක
        
        # User Database: {user_id: {"xp": 0, "messages": 0, "voice_mins": 0, "cooldown": timestamp}}
        self.users = {}
        self.footer_text = "\n\n**💡 Commands:** `.level` | `.leaderboard` | `.voicetime` | `.message leaderboard`"
        
        self.voice_xp_loop.start()

    def get_user(self, uid):
        if uid not in self.users:
            self.users[uid] = {"xp": 0, "messages": 0, "voice_mins": 0, "cooldown": datetime.datetime.min}
        return self.users[uid]

    def get_rank_info(self, xp):
        """XP මත පදනම්ව Rank එක සහ Level එක ගණනය කිරීම"""
        ranks = [
            ("🟤 Bronze", 0, 45000), ("⚪ Silver", 225000, 45000), 
            ("⚫ Obsidian", 450000, 60000), ("🟡 Gold", 750000, 70000),
            ("🔵 Platinum", 1100000, 70000), ("💎 Diamond", 1450000, 70000),
            ("🔥 Master", 1800000, 60000), ("👑 Grandmaster", 2100000, 40000),
            ("⚡ Challenger", 2300000, 25000)
        ]
        
        # Challenger Ascension (Post 2.4M)
        if xp >= 2400000:
            extra_xp = xp - 2400000
            asc_level = int(extra_xp // 100000) + 1
            return "⚡ Challenger (Ascension)", min(asc_level, 16)

        current_rank = "🟤 Bronze"
        current_level = 1

        for name, base_xp, step in ranks:
            if xp >= base_xp:
                current_rank = name
                diff = xp - base_xp
                current_level = int(diff // step) + 1
                if current_level > 5: current_level = 5
            else:
                break
        return current_rank, current_level

    async def check_level_up(self, member, old_xp, new_xp, channel=None):
        old_rank, old_lvl = self.get_rank_info(old_xp)
        new_rank, new_lvl = self.get_rank_info(new_xp)

        if (new_rank != old_rank) or (new_lvl > old_lvl):
            embed = discord.Embed(
                title="🎊 LEVEL UP / RANK UP!",
                description=f"සුභ පැතුම් {member.mention}!\n\n**Rank:** {new_rank}\n**Level:** {new_lvl}",
                color=0x00ff00
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # පණිවිඩ යැවීම
            if channel: await channel.send(embed=embed)
            log_ch = self.bot.get_channel(self.LOG_CH_ID)
            if log_ch: await log_ch.send(f"📈 **{member.name}** reached **{new_rank} - Level {new_lvl}**")
            try: await member.send(f"නියමයි! ඔයා {member.guild.name} හි {new_rank} Level {new_lvl} වුණා! {self.footer_text}")
            except: pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        
        u_data = self.get_user(message.author.id)
        u_data["messages"] += 1
        
        now = datetime.datetime.now()
        if now > u_data["cooldown"]:
            old_xp = u_data["xp"]
            xp_gain = random.randint(10, 20)
            u_data["xp"] += xp_gain
            u_data["cooldown"] = now + datetime.timedelta(seconds=30)
            await self.check_level_up(message.author, old_xp, u_data["xp"], message.channel)

    @tasks.loop(minutes=1)
    async def voice_xp_loop(self):
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    if member.bot: continue
                    u_data = self.get_user(member.id)
                    u_data["voice_mins"] += 1
                    old_xp = u_data["xp"]
                    u_data["xp"] += random.randint(5, 15)
                    await self.check_level_up(member, old_xp, u_data["xp"])

    # --- Commands Section ---

    @commands.command(name="level")
    async def level_cmd(self, ctx, sub: str = None):
        if ctx.channel.id != self.CMD_CH_ID: return
        
        if sub == "leaderboard":
            sorted_users = sorted(self.users.items(), key=lambda x: x[1]['xp'], reverse=True)
            top_member_id, top_data = sorted_users[0]
            top_user = self.bot.get_user(top_member_id)
            rank, lvl = self.get_rank_info(top_data['xp'])
            
            embed = discord.Embed(title="🏆 Level Leaderboard - #1 Member", color=0xffd700)
            embed.description = f"**Name:** {top_user.name if top_user else 'Unknown'}\n**Rank:** {rank}\n**Level:** {lvl}\n**Total XP:** {top_data['xp']:,}"
            await ctx.send(content=self.footer_text, embed=embed)
        else:
            u_data = self.get_user(ctx.author.id)
            rank, lvl = self.get_rank_info(u_data['xp'])
            embed = discord.Embed(title=f"📊 {ctx.author.name}'s Rank", color=0x3498db)
            embed.add_field(name="Current Rank", value=rank, inline=True)
            embed.add_field(name="Level", value=lvl, inline=True)
            embed.add_field(name="Total XP", value=f"{u_data['xp']:,}", inline=False)
            await ctx.send(content=self.footer_text, embed=embed)

    @commands.command(name="voicetime")
    async def voice_cmd(self, ctx, sub: str = None):
        if ctx.channel.id != self.CMD_CH_ID: return
        
        if sub == "leaderboard":
            sorted_v = sorted(self.users.items(), key=lambda x: x[1]['voice_mins'], reverse=True)[:10]
            desc = ""
            for i, (uid, data) in enumerate(sorted_v, 1):
                user = self.bot.get_user(uid)
                desc += f"**{i}.** {user.name if user else uid} - `{data['voice_mins']} mins`\n"
            embed = discord.Embed(title="🎙️ Top 10 Voice Time", description=desc, color=0x1abc9c)
            await ctx.send(content=self.footer_text, embed=embed)
        else:
            u_data = self.get_user(ctx.author.id)
            await ctx.send(f"🎙️ {ctx.author.mention}, ඔයාගේ මුළු Voice කාලය: **{u_data['voice_mins']} minutes.** {self.footer_text}")

    @commands.command(name="message")
    async def msg_leaderboard(self, ctx, sub: str = None):
        if ctx.channel.id != self.CMD_CH_ID or sub != "leaderboard": return
        
        sorted_m = sorted(self.users.items(), key=lambda x: x[1]['messages'], reverse=True)[:10]
        desc = ""
        for i, (uid, data) in enumerate(sorted_m, 1):
            user = self.bot.get_user(uid)
            desc += f"**{i}.** {user.name if user else uid} - `{data['messages']} messages`\n"
        embed = discord.Embed(title="💬 Top 10 Message Count", description=desc, color=0xe67e22)
        await ctx.send(content=self.footer_text, embed=embed)

    @commands.command(name="leaderboard")
    async def all_leaderboards(self, ctx):
        if ctx.channel.id != self.CMD_CH_ID: return
        
        embed = discord.Embed(title="🌟 All Leaderboards Preview", color=0x9b59b6)
        embed.add_field(name="Level", value=f"`.level leaderboard`", inline=True)
        embed.add_field(name="Messages", value=f"`.message leaderboard`", inline=True)
        embed.add_field(name="Voice", value=f"`.voicetime leaderboard`", inline=True)
        await ctx.send(content=self.footer_text, embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
