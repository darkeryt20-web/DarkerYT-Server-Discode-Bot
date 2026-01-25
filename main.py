import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
import os
import asyncio
from google import genai # අලුත් ලයිබ්‍රරි එක

# --- Configuration ---
TOKEN = os.getenv('DISCORD_TOKEN') 
GEMINI_KEY = os.getenv('GEMINI_API_KEY') 
WELCOME_CH_ID = 1463499215954247711
GOODBYE_CH_ID = 1463584100966465596

# --- AI Client Setup ---
client = genai.Client(api_key=GEMINI_KEY)
SYS_MODEL = "gemini-2.0-flash" # අලුත්ම සහ වේගවත්ම Model එක

# --- Bot Setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"❌ Sync Error: {e}")

# --- AI Chat Event ---
@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_input:
            await message.reply("ඔව් මචං, මම අහගෙන ඉන්නේ!")
            return

        async with message.channel.typing():
            try:
                # අලුත් ක්‍රමයට AI පිළිතුර ලබා ගැනීම
                response = client.models.generate_content(
                    model=SYS_MODEL, 
                    contents=user_input,
                    config={'system_instruction': "ඔබේ නම SXD Bot. ඔබ මිත්‍රශීලී සිංහල බොට් කෙනෙකි."}
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"❌ AI Error: {e}")
                await message.reply("සොරි මචං, AI එකේ පොඩි ලෙඩක් ආවා. API Key එක චෙක් කරලා බලන්න.")

    await bot.process_commands(message)

# --- Welcome Card (කලින් තිබූ ලෙසම) ---
async def create_welcome_card(member):
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShzQjsqgvoYier1vQBAMnUWlbr5zq9LC6lFg&s"
    try:
        background = Editor(await load_image_async(bg_url)).resize((800, 450))
        avatar_img = await load_image_async(member.display_avatar.url)
        avatar = Editor(avatar_img).resize((180, 180)).circle_image()
        background.ellipse(position=(310, 90), width=180, height=180, outline="white", stroke_width=5)
        background.paste(avatar, (310, 90))
        font_name = Font.poppins(size=50, variant="bold")
        background.text((400, 300), f"{member.name}", color="#ffffff", font=font_name, align="center")
        return discord.File(fp=background.image_bytes, filename="welcome.png")
    except: return None

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    welcome_file = await create_welcome_card(member)
    if channel and welcome_file:
        await channel.send(file=welcome_file)

# --- Loading Extensions ---
async def load_extensions():
    for extension in ["leveling", "music"]:
        try:
            await bot.load_extension(extension)
            print(f"✅ Loaded: {extension}")
        except Exception as e:
            print(f"❌ Error {extension}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
