import discord
from discord.ext import commands, tasks
from easy_pil import Editor, load_image_async, Font, Canvas
import random
import datetime
import io

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LOG_CH_ID = 1463876659320062086
        self.CMD_CH_ID = 1463878264522014915
        
        # User Database
        self.users = {}
        self.footer_text = "💡 Commands: .level | .leaderboard | .voicetime | .message leaderboard"
        
        self.voice_xp_loop.start()

    def get_user(self, uid):
        if uid not in self.users:
            self.users[uid] = {"xp": 0, "messages": 0, "voice_mins": 0, "cooldown": datetime.datetime.min}
        return self.users[uid]

    def get_rank_info(self, xp):
        # Rank Name, Base XP, Step per Level
        ranks = [
            ("BRONZE", 0, 45000), ("SILVER", 225000, 45000), 
            ("OBSIDIAN", 450000, 60000), ("GOLD", 750000, 70000),
            ("PLATINUM", 1100000, 70000), ("DIAMOND", 1450000, 70000),
            ("MASTER", 1800000, 60000), ("GRANDMASTER", 2100000, 40000),
            ("CHALLENGER", 2300000, 25000)
        ]
        
        if xp >= 2400000:
            extra = xp - 2400000
            asc_lvl = int(extra // 100000) + 1
            return "CHALLENGER ASC.", min(asc_lvl, 16), 2400000 + (asc_lvl * 100000)

        current_rank, current_lvl, next_xp = "BRONZE", 1, 45000
        for name, base, step in ranks:
            if xp >= base:
                current_rank = name
                diff = xp - base
                current_lvl = int(diff // step) + 1
                if current_lvl > 5: current_lvl = 5
                next_xp = base + (current_lvl * step)
            else: break
        return current_rank, current_lvl, next_xp

    async def create_rank_card(self, member, xp, messages, voice):
        rank_name, level, next_xp_req = self.get_rank_info(xp)
        
        # Background නිර්මාණය
        background = Editor(Canvas((900, 250), color="#1e1e1e"))
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((150, 150)).circle_image()
        
        background.paste(avatar, (40, 50))
        
        font_big = Font.poppins(size=40, variant="bold")
        font_small = Font.poppins(size=25, variant="light")
        font_mid = Font.poppins(size=30, variant="regular")

        # විස්තර ඇතුළත් කිරීම
        background.text((220, 50), str(member.name), color="white", font=font_big)
        background.text((220, 100), f"RANK: {rank_name} | LVL: {level}", color="#ffcc00", font=font_mid)
        background.text((220, 150), f"XP: {xp:,} / {next_xp_req:,}", color="#aaaaaa", font=font_small)
        background.text((220, 190), f"MSGS: {messages} | VOICE: {voice}m", color="#aaaaaa", font=font_small)

        # Progress Bar
        percentage = min(int((xp / next_xp_req) * 100), 100) if next_xp_req > 0 else 100
        background.bar((220, 220), max_width=600, height=20, percentage=percentage, fill="#ffcc00", back_color="#444444")

        file = discord.File(fp=background.image_bytes, filename="rank.png")
        return file

    async def check_level_up(self, member, old_xp, new_xp, channel=None):
        old_r, old_l, _ = self.get_rank_info(old_xp)
        new_r, new_l, _ = self.get_rank_info(new_xp)

        if (new_r != old_r) or (new_l > old_l):
            card = await self.create_rank_card(member, new_xp, self.users[member.id]["messages"], self.users[member.id]["voice_mins"])
            msg = f"🎊 {member.mention} Upgraded to **{new_r} Level {new_l}**!"
            
            if channel: await channel.send(content=msg, file=card)
            log_ch = self.bot.get_channel(self.LOG_CH_ID)
            if log_ch: await log_ch.send(f"📈 **{member.name}** -> {new_r} Lvl {new_l}")
            try: await member.send(content=f"You leveled up in {member.guild.name}!", file=card)
            except: pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        u_data = self.get_user(message.author.id)
        u_data["messages"] += 1
        
        now = datetime.datetime.now()
        if now > u_data["cooldown"]:
            old_xp = u_data["xp"]
            u_data["xp"] += random.randint(10, 20)
            u_data["cooldown"] = now + datetime.timedelta(seconds=30)
            await self.check_level_up(message.author, old_xp, u_data["xp"], message.channel)

    @tasks.loop(minutes=1)
    async def voice_xp_loop(self):
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for m in vc.members:
                    if m.bot: continue
                    u = self.get_user(m.id)
                    u["voice_mins"] += 1
                    old_xp = u["xp"]
                    u["xp"] += random.randint(5, 15)
                    await self.check_level_up(m, old_xp, u["xp"])

    @commands.command(name="level")
    async def level_cmd(self, ctx, sub: str = None):
        if ctx.channel.id != self.CMD_CH_ID: return
        
        if sub == "leaderboard":
            sorted_users = sorted(self.users.items(), key=lambda x: x[1]['xp'], reverse=True)
            top_id, top_data = sorted_users[0]
            top_user = await self.bot.fetch_user(top_id)
            card = await self.create_rank_card(top_user, top_data['xp'], top_data['messages'], top_data['voice_mins'])
            await ctx.send(content=f"🏆 **#1 Member Leaderboard**\n{self.footer_text}", file=card)
        else:
            u = self.get_user(ctx.author.id)
            card = await self.create_rank_card(ctx.author, u['xp'], u['messages'], u['voice_mins'])
            await ctx.send(content=self.footer_text, file=card)

    @commands.command(name="voicetime")
    async def voice_cmd(self, ctx, sub: str = None):
        if ctx.channel.id != self.CMD_CH_ID: return
        u = self.get_user(ctx.author.id)
        if sub == "leaderboard":
            sorted_v = sorted(self.users.items(), key=lambda x: x[1]['voice_mins'], reverse=True)[:10]
            res = "\n".join([f"**{i+1}.** <@{uid}> - `{d['voice_mins']}m`" for i, (uid, d) in enumerate(sorted_v)])
            await ctx.send(embed=discord.Embed(title="🎙️ Voice Leaderboard", description=res + f"\n\n{self.footer_text}"))
        else:
            await ctx.send(f"🎙️ {ctx.author.mention}, Total Voice Time: **{u['voice_mins']}m**\n{self.footer_text}")

    @commands.command(name="message")
    async def msg_cmd(self, ctx, sub: str = None):
        if ctx.channel.id != self.CMD_CH_ID or sub != "leaderboard": return
        sorted_m = sorted(self.users.items(), key=lambda x: x[1]['messages'], reverse=True)[:10]
        res = "\n".join([f"**{i+1}.** <@{uid}> - `{d['messages']} msgs`" for i, (uid, d) in enumerate(sorted_m)])
        await ctx.send(embed=discord.Embed(title="💬 Message Leaderboard", description=res + f"\n\n{self.footer_text}"))

    @commands.command(name="leaderboard")
    async def lb_all(self, ctx):
        if ctx.channel.id != self.CMD_CH_ID: return
        await ctx.send(f"🌟 **Available Leaderboards:**\n`.level leaderboard` | `.message leaderboard` | `.voicetime leaderboard` \n\n{self.footer_text}")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
