import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')

async def create_welcome_card(member):
    # 1. Background Image එක load කිරීම
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
    background = Editor(await load_image_async(bg_url)).resize((800, 450))
    
    # 2. Avatar එක සැකසීම
    avatar_img = await load_image_async(member.display_avatar.url)
    avatar = Editor(avatar_img).resize((180, 180)).circle_image()
    
    # 3. Decoration (Avatar එක වටේට රවුම ඇඳීම)
    # මීට කලින් ආපු AttributeError එක මෙතනින් fix කරලා තියෙනවා
    background.ellipse((310, 90), 180, 180, outline="white", width=5)
    
    # Avatar එක මැදට paste කිරීම
    background.paste(avatar, (310, 90))
    
    # 4. Fonts සැකසීම
    try:
        # Koyeb වල fonts නැති වුනොත් error එකක් එන එක වැලැක්වීමට try/except පාවිච්චි කරමු
        font_name = Font.poppins(size=50, variant="bold")
        font_sub = Font.poppins(size=30, variant="light")
    except:
        font_name = None 
        font_sub = None

    # 5. නම සහ විස්තර (Center alignment)
    background.text((400, 300), f"{member.name}", color="#ffffff", font=font_name, align="center")
    background.text((400, 360), "WELCOME TO THE SERVER", color="#ffcc00", font=font_sub, align="center")
    background.text((400, 400), f"Member #{member.guild.member_count}", color="#aaaaaa", font=font_sub, align="center")
    
    return discord.File(fp=background.image_bytes, filename="welcome.png")

@bot.event
async def on_member_join(member):
    print(f"DEBUG: {member.name} join වුණා, Card එක හදනවා...")
    channel = bot.get_channel(WELCOME_CH_ID)
    
    try:
        # Card එක සාදා ගැනීම
        welcome_file = await create_welcome_card(member)
        
        # Server එකට Embed එක සහ Image එක යැවීම
        if channel:
            embed = discord.Embed(
                title="✨ New Member Joined!",
                description=f"Welcome {member.mention} to **{member.guild.name}**!",
                color=0x2f3136
            )
            embed.set_image(url="attachment://welcome.png")
            await channel.send(file=welcome_file, embed=embed)
            print(f"✅ Server welcome message sent for {member.name}")

        # Private Message (DM) එකට යැවීම
        try:
            # DM එකට වෙනම file එකක් ඕනේ (Discord limitation)
            dm_file = await create_welcome_card(member)
            dm_embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hi {member.name}, check out your welcome card!",
                color=discord.Color.blue()
            )
            dm_embed.set_image(url="attachment://welcome.png")
            await member.send(file=dm_file, embed=dm_embed)
            print(f"✅ DM sent to {member.name}")
        except Exception as dm_err:
            print(f"⚠️ DM එක යවන්න බැරි වුණා: {dm_err}")

    except Exception as e:
        print(f"❌ Welcome Error: {e}")
        # මොකක් හරි වැරදුනොත් අඩුම තරමේ text එක හරි යවන්න
        if channel:
            await channel.send(f"Welcome to the server, {member.mention}!")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"Goodbye **{member.name}**! We hope to see you again soon.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

bot.run(TOKEN)
