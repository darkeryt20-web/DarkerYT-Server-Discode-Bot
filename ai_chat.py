import discord
from discord.ext import commands
import google.generativeai as genai
import os

# Gemini AI Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # බොට්ව mention කළොත් හෝ Reply කළොත් විතරක් AI එක වැඩ කරයි
        if self.bot.user.mentioned_in(message) and not message.author.bot:
            # Mention එක අයින් කරලා ප්‍රශ්නය විතරක් ගැනීම
            user_input = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            
            if not user_input:
                return await message.reply("ඔව් මචං, කියන්න? මම ඔයාට කොහොමද උදව් කරන්නේ?")

            async with message.channel.typing():
                try:
                    # AI එකෙන් පිළිතුර ලබා ගැනීම
                    response = model.generate_content(user_input)
                    reply_text = response.text
                    
                    # Discord වල message limit එක (2000 characters) පරීක්ෂාව
                    if len(reply_text) > 2000:
                        reply_text = reply_text[:1990] + "..."
                        
                    await message.reply(reply_text)
                except Exception as e:
                    print(f"❌ AI Error: {e}")
                    await message.reply("සොරි මචං, පොඩි error එකක් ආවා. පස්සේ ට්‍රයි කරමුද?")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
