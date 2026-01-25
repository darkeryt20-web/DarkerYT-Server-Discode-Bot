import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1463584100966465596
        self.OWNER_ID = 1391883050035581148

    async def generate_leave_card(self, member):
        # Design Setup (Using a slightly different dark theme for leave)
        bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
        try:
            background = Editor(await load_image_async(bg_url)).resize((800, 450))
            
            # User Avatar with a Red/Grey outline for Goodbye
            avatar_img = await load_image_async(member.display_avatar.url)
            avatar = Editor(avatar_img).resize((160, 160)).circle_image()
            
            background.ellipse(position=(320, 70), width=160, height=160, outline="#ff4b4b", stroke_width=4)
            background.paste(avatar, (320, 70))
            
            # Fonts
            font_big = Font.poppins(size=40, variant="bold")
            font_small = Font.poppins(size=25, variant="light")
            font_msg = Font.poppins(size=20, variant="italic")

            # Texts
            background.text((400, 260), "GOODBYE", color="#ff4b4b", font=font_small, align="center")
            background.text((400, 310), f"{member.name}", color="white", font=font_big, align="center")
            background.text((400, 370), "We hope to see you again soon!", color="#aaaaaa", font=font_msg, align="center")
            
            return discord.File(fp=background.image_bytes, filename="leave_card.png")
        except Exception as e:
            print(f"❌ Leave Image Error: {e}")
            return None

    @commands.command(name="leave")
    async def test_leave(self, ctx):
        """Owner only preview of the leave card"""
        if ctx.author.id != self.OWNER_ID:
            return

        file = await self.generate_leave_card(ctx.author)
        embed = discord.Embed(
            title="👋 Leave Card Preview",
            description="This is how the goodbye message will appear.",
            color=discord.Color.red()
        )
        if file:
            embed.set_image(url="attachment://leave_card.png")
            await ctx.send(file=file, embed=embed, delete_after=30)
        else:
            await ctx.send("Error generating card.", delete_after=5)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if not channel:
            return

        file = await self.generate_leave_card(member)
        embed = discord.Embed(
            title="A Member Has Left",
            description=f"Goodbye **{member.name}**! Thank you for being part of our server.",
            color=discord.Color.red()
        )
        
        if file:
            embed.set_image(url="attachment://leave_card.png")
            await channel.send(file=file, embed=embed)
        else:
            # Fallback if image fails
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leave(bot))
