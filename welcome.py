import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1463499215954247711

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.CHANNEL_ID)
        if not channel: return

        bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
        try:
            background = Editor(await load_image_async(bg_url)).resize((800, 450))
            avatar_img = await load_image_async(member.display_avatar.url)
            avatar = Editor(avatar_img).resize((180, 180)).circle_image()
            
            background.ellipse(position=(310, 90), width=180, height=180, outline="white", stroke_width=5)
            background.paste(avatar, (310, 90))
            
            font = Font.poppins(size=50, variant="bold")
            # Text on Image
            background.text((400, 320), f"WELCOME", color="white", font=font, align="center")
            background.text((400, 380), f"{member.name}", color="#ffcc00", font=font, align="center")

            file = discord.File(fp=background.image_bytes, filename="welcome.png")
            
            # Embed Message
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hello {member.mention}, we are happy to have you here.",
                color=0x2f3136
            )
            embed.set_image(url="attachment://welcome.png")
            
            await channel.send(file=file, embed=embed)
        except Exception as e:
            print(f"❌ Welcome Card Error: {e}")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
