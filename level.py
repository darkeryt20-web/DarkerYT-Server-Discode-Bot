import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import json
import os

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.OWNER_ID = 1391883050035581148
        self.COMMAND_CH_ID = 1463878264522014915
        self.data_file = "levels.json"
        self.users = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.users, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        author_id = str(message.author.id)
        if author_id not in self.users:
            self.users[author_id] = {"xp": 0, "level": 0, "master_level": "Novice"}

        # XP Increment
        self.users[author_id]["xp"] += 5
        xp = self.users[author_id]["xp"]
        lvl = self.users[author_id]["level"]

        # Level Up Logic (XP needed = level * 100)
        if xp >= (lvl + 1) * 100:
            self.users[author_id]["level"] += 1
            self.users[author_id]["xp"] = 0
            new_lvl = self.users[author_id]["level"]
            
            # Master Level Update
            if new_lvl >= 50: self.users[author_id]["master_level"] = "Grand Master"
            elif new_lvl >= 20: self.users[author_id]["master_level"] = "Expert"
            elif new_lvl >= 10: self.users[author_id]["master_level"] = "Pro"
            elif new_lvl >= 5: self.users[author_id]["master_level"] = "Elite"

            self.save_data()
            
            # Level Up Message
            try:
                embed = discord.Embed(
                    title="Level Up! 🆙",
                    description=f"Congratulations {message.author.mention}!\nYou reached **Level {new_lvl}** ({self.users[author_id]['master_level']})",
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed, delete_after=10)
            except: pass
        else:
            self.save_data()

    async def generate_rank_card(self, member, xp, lvl, master):
        bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
        background = Editor(await load_image_async(bg_url)).resize((800, 250))
        
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((120, 120)).circle_image()
        background.paste(avatar, (40, 65))

        font_big = Font.poppins(size=35, variant="bold")
        font_small = Font.poppins(size=20, variant="light")

        # Progress Bar Logic
        next_xp = (lvl + 1) * 100
        background.rectangle((200, 170), width=550, height=30, fill="#444444", radius=15)
        bar_width = int((xp / next_xp) * 550)
        if bar_width > 0:
            background.rectangle((200, 170), width=bar_width, height=30, fill="#ffcc00", radius=15)

        # Texts
        background.text((200, 60), member.name, color="white", font=font_big)
        background.text((200, 110), f"Level: {lvl} | {master}", color="#aaaaaa", font=font_small)
        background.text((750, 140), f"{xp}/{next_xp} XP", color="white", font=font_small, align="right")

        return discord.File(fp=background.image_bytes, filename="rank.png")

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        if ctx.channel.id != self.COMMAND_CH_ID and ctx.author.id != self.OWNER_ID:
            return await ctx.send(f"❌ Please use <#{self.COMMAND_CH_ID}>", delete_after=5)

        user_id = str(member.id)
        if user_id not in self.users:
            return await ctx.send("No rank data found for this user.")

        data = self.users[user_id]
        file = await self.generate_rank_card(member, data["xp"], data["level"], data["master_level"])
        await ctx.send(file=file)

    @commands.command(name="level")
    async def level_preview(self, ctx):
        """Owner only preview of rank card"""
        if ctx.author.id != self.OWNER_ID: return
        await self.rank(ctx)

async def setup(bot):
    await bot.add_cog(Level(bot))
