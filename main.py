import discord
from discord.ext import commands
import os
from github import Github
from datetime import datetime

# Settings
TOKEN = os.getenv('DISCORD_TOKEN')
GH_TOKEN = os.getenv('GH_TOKEN') # Koyeb එකේ සෙට් කරන්න
REPO_NAME = "ඔයාගේ_Github_නම/Repo_නම" # උදා: DarkerYT/my-bot-web

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

def update_github_web(name, avatar_url):
    try:
        g = Github(GH_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents("index.html")
        
        # දැනට තියෙන HTML එක ගන්න
        old_html = contents.decoded_content.decode("utf-8")
        
        # අලුත් member පේළිය (Row)
        join_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = f"<tr><td><img src='{avatar_url}' width='50'></td><td>{name}</td><td>{join_time}</td></tr>\n"
        
        # </table> ටැග් එකට උඩින් අලුත් පේළිය ඇතුළත් කිරීම
        updated_html = old_html.replace("</table>", f"{new_row}</table>")
        
        # GitHub එකට සේව් කිරීම (Commit)
        repo.update_file(contents.path, f"New member: {name}", updated_html, contents.sha)
        print(f"✅ GitHub Web Updated for {name}")
    except Exception as e:
        print(f"❌ GitHub Update Error: {e}")

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')

@bot.event
async def on_member_join(member):
    # GitHub එක update කිරීම
    update_github_web(member.name, member.display_avatar.url)
    
    # Welcome message එක යැවීම (කලින් හදපු image code එක මෙතනට දාන්න)
    channel = bot.get_channel(1463499215954247711)
    if channel:
        await channel.send(f"Welcome {member.mention}! විස්තර වෙබ් අඩවියට එකතු කළා.")

bot.run(TOKEN)
