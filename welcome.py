import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1463499215954247711
        self.OWNER_ID = 1391883050035581148

    async def generate_card(self, member):
        # Design Setup
        bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
        background = Editor(await load_image_async(bg_url)).resize((800, 450))
        
        # User Avatar
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((160, 160)).circle_image()
        
        # Server Logo (Upgraded)
        if member.guild.icon:
            logo_img = await load_image_async(member.guild.icon.url)
            logo = Editor(logo_img).resize((80, 80)).circle_image()
            background.paste(logo, (700, 20)) # Top right corner

        # Background Decoration
        background.ellipse(position=(320, 70), width=160, height=160, outline="white", stroke_width=4)
        background.paste(avatar, (320, 70))
        
        # Fonts
        font_big = Font.poppins(size=40, variant="bold")
        font_small = Font.poppins(size=25, variant="light")
        font_rank = Font.poppins(size=20, variant="italic")

        # Texts
        background.text((400, 260), "WELCOME", color="white", font=font_small, align="center")
        background.text((400, 310), f"{member.name}", color="#ffcc00", font=font_big, align="center")
        background.text((400, 360), f"Member #{member.guild.member_count}", color="#aaaaaa", font=font_rank, align="center")
        background.text((400, 400), f"Welcome to {member.guild.name}", color="white", font=font_small, align="center")

        return discord.File(fp=background.image_bytes, filename="welcome_card.png")

    @commands.command(name="come")
    async def test_come(self, ctx):
        if ctx.author.id != self.OWNER_ID:
            return

        file = await self.generate_card(ctx.author)
        embed = discord.Embed(
            title="✨ Welcome Card Preview",
            description="This is how the new member will see the card.",
            color=0x2b2d31
        )
        embed.set_image(url="attachment://welcome_card.png")
        await ctx.send(file=file, embed=embed, delete_after=30)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # 1. Send to Server Channel
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if channel:
            file = await self.generate_card(member)
            embed = discord.Embed(
                title="A New Member Arrived!",
                description=f"Welcome {member.mention}! Enjoy your stay in **{member.guild.name}**.",
                color=0x5865F2
            )
            embed.set_image(url="attachment://welcome_card.png")
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(file=file, embed=embed)

        # 2. Send Personal DM to User (Upgrade)
        try:
            dm_embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hey {member.name}, thanks for joining us! Please check the rules channel.",
                color=0x5865F2
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"Could not DM {member.name} (DMs are closed).")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
