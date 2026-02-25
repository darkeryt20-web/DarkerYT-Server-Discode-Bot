import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1474041097498923079
        self.bg_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/background.jpg"
        self.logo_url = "https://raw.githubusercontent.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/main/Copilot_20260223_123057.png"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return

        # --- Welcome Card Generation ---
        try:
            background = await load_image_async(self.bg_url)
            editor = Editor(background).resize((800, 450)) # Standard Card Size
            
            # Member Profile Image (Center)
            avatar = await load_image_async(str(member.display_avatar.url))
            editor.draw_image(avatar, (300, 100), size=(200, 200), circular=True)
            
            # Custom Fonts & Text
            font_big = Font.poppins(size=40, variant="bold")
            font_small = Font.poppins(size=25, variant="light")

            editor.text((400, 320), f"WELCOME {member.name.upper()}", color="white", font=font_big, align="center")
            editor.text((400, 370), "Enjoy your stay in our network!", color="#aaaaaa", font=font_small, align="center")

            file = discord.File(fp=editor.image_bytes, filename="welcome.png")

            # --- Embed Creation ---
            embed = discord.Embed(
                title="👋 Welcome to 𝙎𝙓𝘿 𝙑𝙋𝙉 - 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙉𝙚𝙩𝙬𝙤𝙧𝙠 𝙁𝙡𝙖𝙨𝙝 𝘿𝙚𝙖𝙡𝙨!",
                description=f"👋 Hello {member.mention},\n📌 Please read the rules and enjoy your stay!",
                color=0x2f3136
            )
            embed.set_image(url="attachment://welcome.png")
            embed.set_footer(text="Powered By 𝙎𝙓𝘿", icon_url=self.logo_url)

            await channel.send(content=f"Welcome {member.mention}!", embed=embed, file=file)
            
        except Exception as e:
            print(f"Error generating welcome card: {e}")
            # Fallback if image fails
            await channel.send(f"Welcome to the server, {member.mention}!")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
