import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os
import asyncio

# --- 1. Configuration ---
# Koyeb Environment Variables වල මේවා නිවැරදිව ඇතුළත් කර ඇති බව සහතික කරගන්න
TOKEN = os.getenv('DISCORD_TOKEN') 
WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

# --- 2. Bot Setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')
    
    # Slash Commands (Music /play, etc.) Sync කිරීම
    try:
        print("🔄 Syncing slash commands...")
        synced = await bot.tree.sync()
        print(f"🚀 Successfully synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Slash Sync Error: {e}")

# --- 3. Welcome Card Logic ---
async def create_welcome_card(member):
    # Background රූපය
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
    
    try:
        # රූප සැකසීම (easy-pil භාවිතයෙන්)
        background = Editor(await load_image_async(bg_url)).resize((800, 450))
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((180, 180)).circle_image()
        
        # Avatar එක මැදට ගැනීම සහ Outline එක ඇඳීම
        background.ellipse(position=(310, 90), width=180, height=180, outline="white", stroke_width=5)
        background.paste(avatar, (310, 90))
        
        # අකුරු (Fonts)
        font_name = Font.poppins(size=50, variant="bold")
        font_sub = Font.poppins(size=30, variant="light")

        background.text((400, 300), f"{member.name}", color="#ffffff", font=font_name, align="center")
        background.text((400, 360), "WELCOME TO THE SERVER", color="#ffcc00", font=font_sub, align="center")
        background.text((400, 400), f"Member #{member.guild.member_count}", color="#aaaaaa", font=font_sub, align="center")
        
        return discord.File(fp=background.image_bytes, filename="welcome.png")
    except Exception as e:
        print(f"⚠️ Welcome Card Error: {e}")
        return None

# --- 4. Member Events (Join/Leave) ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    welcome_file = await create_welcome_card(member)
    
    if channel and welcome_file:
        embed = discord.Embed(
            title="✨ New Member Joined!",
            description=f"Welcome {member.mention} to **{member.guild.name}**!",
            color=0x2f3136
        )
        embed.set_image(url="attachment://welcome.png")
        await channel.send(file=welcome_file, embed=embed)

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

# --- 5. Extensions Loading ---
async def load_extensions():
    # GitHub එකේ මේ files 2ම තිබිය යුතුයි: leveling.py, music.py
    initial_extensions = ["leveling", "music"]
    
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"✅ Extension Loaded: {extension}")
        except Exception as e:
            print(f"❌ Failed to load extension {extension}: {e}")

# --- 6. Execution ---
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔴 Bot is shutting down...")
