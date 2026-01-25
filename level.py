import discord
from discord.ext import commands, tasks
from easy_pil import Editor, load_image_async, Font
import json
import os
import random

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- CONFIGURATION (ID TIKA) ---
        self.CMD_CHANNEL_ID = 1463878264522014915   # Commands wada karana channel eka
        self.LEVEL_LOG_CH = 1463876659320062086     # Level up logs yana channel eka
        
        self.data_file = "levels.json"
        self.users = self.load_data()
        self.voice_xp_loop.start() # Voice XP loop start

    # --- DATA HANDLING ---
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.users, f, indent=4)

    # --- RANK TITLES ---
    def get_rank_title(self, level):
        if level >= 350: return "Legendary"
        elif level >= 300: return "Master"
        elif level >= 250: return "Diamond"
        elif level >= 200: return "Platinum"
        elif level >= 150: return "Gold"
        elif level >= 100: return "Obsidian" 
        elif level >= 50: return "Silver"
        return "Bronze"

    def get_xp_for_next_level(self, level):
        return 44 * ((level + 1) ** 2)

    # --- VOICE XP LOOP (Every 1 Minute) ---
    @tasks.loop(minutes=1)
    async def voice_xp_loop(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.voice and not member.bot:
                    if not member.voice.self_mute and not member.voice.self_deaf:
                        user_id = str(member.id)
                        if user_id not in self.users:
                            self.users[user_id] = {"xp": 0, "level": 0, "msg_count": 0, "voice_min": 0}
                        
                        xp_gain = random.randint(15, 20)
                        self.users[user_id]["xp"] += xp_gain
                        self.users[user_id]["voice_min"] += 1
                        
                        await self.check_level_up(member, user_id)
        self.save_data()

    @voice_xp_loop.before_loop
    async def before_voice_loop(self):
        await self.bot.wait_until_ready()

    # --- LEVEL UP CHECK ---
    async def check_level_up(self, member, user_id):
        current_xp = self.users[user_id]["xp"]
        current_lvl = self.users[user_id]["level"]
        next_lvl_xp = self.get_xp_for_next_level(current_lvl)

        if current_xp >= next_lvl_xp:
            self.users[user_id]["level"] += 1
            new_lvl = self.users[user_id]["level"]
            rank_name = self.get_rank_title(new_lvl)
            self.save_data()

            # 1. Personal DM
            try:
                embed_dm = discord.Embed(title="🎉 Level Up!", description=f"You reached **Level {new_lvl}** ({rank_name})!", color=discord.Color.gold())
                await member.send(embed=embed_dm)
            except: pass

            # 2. Log Channel Message
            channel = self.bot.get_channel(self.LEVEL_LOG_CH)
            if channel:
                embed_log = discord.Embed(
                    title="🆙 Level Upgrade",
                    description=f"{member.mention} has reached **Level {new_lvl}**!",
                    color=discord.Color.green()
                )
                embed_log.set_thumbnail(url=member.display_avatar.url)
                embed_log.add_field(name="Rank", value=rank_name)
                await channel.send(embed=embed_log)

    # --- CHAT XP SYSTEM ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return

        # Delete user command messages in CMD channel (after 10s)
        if message.channel.id == self.CMD_CHANNEL_ID and message.content.startswith('.'):
            await message.delete(delay=10)

        user_id = str(message.author.id)
        if user_id not in self.users:
            self.users[user_id] = {"xp": 0, "level": 0, "msg_count": 0, "voice_min": 0}

        # XP Logic based on length
        length = len(message.content)
        if length < 20:
            xp_gain = random.randint(10, 25)
        elif length < 100:
            xp_gain = random.randint(50, 75)
        else:
            xp_gain = random.randint(80, 100)

        self.users[user_id]["xp"] += xp_gain
        self.users[user_id]["msg_count"] += 1
        
        await self.check_level_up(message.author, user_id)
        self.save_data()

    # --- IMAGE GENERATOR ---
    async def generate_rank_card(self, member, xp, lvl, rank_name, needed_xp):
        bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
        background = Editor(await load_image_async(bg_url)).resize((800, 250))
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((130, 130)).circle_image()
        background.paste(avatar, (50, 60))

        percentage = min(xp / needed_xp, 1)
        background.rectangle((220, 180), width=520, height=30, fill="#404040", radius=15)
        background.rectangle((220, 180), width=int(520 * percentage), height=30, fill="#00ffcc", radius=15)

        font_name = Font.poppins(size=40, variant="bold")
        font_det = Font.poppins(size=25, variant="light")
        
        background.text((220, 70), member.name, color="white", font=font_name)
        background.text((220, 130), f"Level: {lvl} | Rank: {rank_name}", color="#ffcc00", font=font_det)
        background.text((740, 140), f"{xp} / {needed_xp} XP", color="white", font=font_det, align="right")

        return discord.File(fp=background.image_bytes, filename="rank.png")

    # --- HELPER: SEND COMMAND LIST ---
    async def send_help_card(self, ctx):
        embed = discord.Embed(title="🤖 Bot Commands", color=discord.Color.blue())
        embed.add_field(name="📊 Stats", value="`.Rank` `.Level` - Check your stats", inline=False)
        embed.add_field(name="🏆 Leaderboards", value="`.Top` `.TopLevel`\n`.TopVoice`\n`.TopMessage`", inline=False)
        await ctx.send(embed=embed)

    # --- COMMANDS ---
    @commands.command(aliases=["level", "Level", "Rank"])
    async def rank(self, ctx, member: discord.Member = None):
        if ctx.channel.id != self.CMD_CHANNEL_ID: return
        member = member or ctx.author
        user_id = str(member.id)
        
        if user_id not in self.users: return await ctx.send("No data yet!", delete_after=5)

        data = self.users[user_id]
        needed_xp = self.get_xp_for_next_level(data["level"])
        rank_name = self.get_rank_title(data["level"])

        file = await self.generate_rank_card(member, data["xp"], data["level"], rank_name, needed_xp)
        await ctx.send(file=file)
        await self.send_help_card(ctx)

    @commands.command(aliases=["Top", "toplevel", "TopLevel"])
    async def top(self, ctx):
        if ctx.channel.id != self.CMD_CHANNEL_ID: return
        sorted_users = sorted(self.users.items(), key=lambda x: x[1]['level'], reverse=True)[:10]
        
        embed = discord.Embed(title="🏆 Top 10 Levels", color=discord.Color.gold())
        for i, (uid, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(int(uid))
            name = user.name if user else "Unknown"
            embed.add_field(name=f"#{i} {name}", value=f"Lvl {data['level']} | {self.get_rank_title(data['level'])}", inline=False)
        await ctx.send(embed=embed)
        await self.send_help_card(ctx)

    @commands.command(aliases=["TopVoice"])
    async def topvoice(self, ctx):
        if ctx.channel.id != self.CMD_CHANNEL_ID: return
        sorted_users = sorted(self.users.items(), key=lambda x: x[1].get('voice_min', 0), reverse=True)[:10]
        embed = discord.Embed(title="🎙️ Top Voice Users", color=discord.Color.purple())
        for i, (uid, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(int(uid))
            name = user.name if user else "Unknown"
            embed.add_field(name=f"#{i} {name}", value=f"{data.get('voice_min', 0)} Minutes", inline=False)
        await ctx.send(embed=embed)
        await self.send_help_card(ctx)

    @commands.command(aliases=["TopMessage"])
    async def topmessage(self, ctx):
        if ctx.channel.id != self.CMD_CHANNEL_ID: return
        sorted_users = sorted(self.users.items(), key=lambda x: x[1].get('msg_count', 0), reverse=True)[:10]
        embed = discord.Embed(title="💬 Top Chatters", color=discord.Color.teal())
        for i, (uid, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(int(uid))
            name = user.name if user else "Unknown"
            embed.add_field(name=f"#{i} {name}", value=f"{data.get('msg_count', 0)} Messages", inline=False)
        await ctx.send(embed=embed)
        await self.send_help_card(ctx)

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        if ctx.channel.id != self.CMD_CHANNEL_ID: return
        await self.send_help_card(ctx)

async def setup(bot):
    await bot.add_cog(Level(bot))
