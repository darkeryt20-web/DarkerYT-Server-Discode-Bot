import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os

# Koyeb Variables වල DISCORD_TOKEN ලෙස මෙය තිබිය යුතුයි
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel IDs
WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')

# --- සාමාජිකයෙකු Join වූ විට ---
@bot.event
async def on_member_join(member):
    # 1. Server එකට Image එකක් යැවීම
    channel = bot.get_channel(WELCOME_CH_ID)
    if channel:
        try:
            bg_url = "https://i.imgur.com/8Yv9X6X.jpg" 
            background = Editor(await load_image_async(bg_url)).resize((800, 450))
            avatar_img = await load_image_async(member.display_avatar.url)
            avatar = Editor(avatar_img).resize((150, 150)).circle_image()
            background.paste(avatar, (325, 100))
            
            try:
                font_big = Font.poppins(size=45, variant="bold")
            except:
                font_big = None

            background.text((400, 280), "WELCOME", color="white", font=font_big, align="center")
            background.text((400, 335), f"{member.name}", color="#ffcc00", font=font_big, align="center")
            
            file = discord.File(fp=background.image_bytes, filename="welcome.png")
            await channel.send(content=f"Welcome {member.mention}! ❤️", file=file)
        except Exception as e:
            print(f"Server message error: {e}")
            await channel.send(f"Welcome {member.mention}!")

    # 2. Personal Message (DM) එකක් යැවීම
    try:
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=f"Hi {member.name}, thanks for joining our server! Please read the rules and enjoy your stay.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
        await member.send(embed=embed)
        print(f"✅ DM sent to {member.name}")
    except discord.Forbidden:
        print(f"❌ Cannot send DM to {member.name} (Privacy settings)")

# --- සාමාජිකයෙකු Leave වූ විට ---
@bot.event
async def on_member_remove(member):
    # 1. Server එකට Message එකක් යැවීම
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"Goodbye **{member.name}**! 👋")

    # 2. Personal Message (DM) එකක් යැවීම
    try:
        await member.send(f"Goodbye {member.name}. We are sorry to see you leave **{member.guild.name}** server. Hope to see you back soon!")
    except discord.Forbidden:
        pass # User DM block කර ඇත්නම් silent ව සිටින්න

bot.run(TOKEN)
