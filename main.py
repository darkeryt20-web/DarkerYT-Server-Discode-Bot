import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os
import asyncio
import google.generativeai as genai  # AI සඳහා

# --- 1. Configuration ---
TOKEN = os.getenv('DISCORD_TOKEN') 
GEMINI_KEY = os.getenv('GEMINI_API_KEY') # API Key එක මෙතනට
WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

# AI Configuration
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # වේගවත් මාදිලිය

# --- 2. Bot Setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')
    try:
        await bot.tree.sync()
        print(f"🚀 Slash commands synced.")
    except Exception as e:
        print(f"❌ Sync Error: {e}")

# --- 3. AI Chat Logic ---
@bot.event
async def on_message(message):
    # බොට්ව Mention කරලා තියෙනවා නම් සහ message එක එව්වේ Bot කෙනෙක් නෙවෙයි නම්
    if bot.user.mentioned_in(message) and not message.author.bot:
        # User ගේ ප්‍රශ්නයෙන් mention එක අයින් කිරීම
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_input:
            await message.reply("ඔව් මචං, මම අහගෙන ඉන්නේ! මොකක් හරි දැනගන්න ඕනෙද?")
            return

        async with message.channel.typing():
            try:
                # AI උත්තරය ලබා ගැනීම
                response = model.generate_content(user_input)
                await message.reply(response.text)
            except Exception as e:
                print(f"❌ AI Error: {e}")
                await message.reply("සොරි මචං, මගේ AI සිස්ටම් එකේ පොඩි අවුලක් ආවා.")

    # Commands වැඩ කිරීමට මෙය අනිවාර්යයි
    await bot.process_commands(message)

# --- 4. Welcome Card Logic ---
async def create_welcome_card(member):
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
    try:
        background = Editor(await load_image_async(bg_url)).resize((800, 450))
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((180, 180)).circle_image()
        background.ellipse(position=(310, 90), width=180, height=180, outline="white", stroke_width=5)
        background.paste(avatar, (310, 90))
        
        font_name = Font.poppins(size=50, variant="bold")
        font_sub = Font.poppins(size=30, variant="light")
        background.text((400, 300), f"{member.name}", color="#ffffff", font=font_name, align="center")
        background.text((400, 360), "WELCOME TO THE SERVER", color="#ffcc00", font=font_sub, align="center")
        background.text((400, 400), f"Member #{member.guild.member_count}", color="#aaaaaa", font=font_sub, align="center")
        return discord.File(fp=background.image_bytes, filename="welcome.png")
    except Exception as e:
        print(f"⚠️ Welcome Card Error: {e}")
        return None

# --- 5. Member Events ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    welcome_file = await create_welcome_card(member)
    if channel and welcome_file:
        embed = discord.Embed(title="✨ New Member Joined!", description=f"Welcome {member.mention}!", color=0x2f3136)
        embed.set_image(url="attachment://welcome.png")
        await channel.send(file=welcome_file, embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CH_ID)
    if channel:
        await channel.send(f"👋 **{member.name}** left the server.")

# --- 6. Extensions Loading ---
async def load_extensions():
    # 'leveling' සහ 'music' පමණක් load කරයි
    for extension in ["leveling", "music"]:
        try:
            await bot.load_extension(extension)
            print(f"✅ Extension Loaded: {extension}")
        except Exception as e:
            print(f"❌ Failed to load {extension}: {e}")

# --- 7. Run Bot ---
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
