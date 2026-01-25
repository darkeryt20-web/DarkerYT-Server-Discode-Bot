import discord
from discord.ext import commands, tasks
import asyncio

# FFmpeg settings (GitHub MP3 links වලට ගැලපෙන ලෙස)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TARGET_CHANNEL_ID = 1463845234239606985
        
        # --- මෙතනට ඔයාගේ GitHub Raw MP3 Links ටික දාන්න ---
        self.playlist = [
            "https://github.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/edit/main/music1.mp3",
            "https://github.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/edit/main/music2.mp3",
            "https://github.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/edit/main/music3.mp3",
            "https://github.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/edit/main/music4.mp3",
            "https://github.com/darkeryt20-web/DarkerYT-Server-Discode-Bot/edit/main/music5.mp3"
        ]
        
        self.current_index = 0
        self.auto_play_loop.start()

    @tasks.loop(seconds=5)
    async def auto_play_loop(self):
        if not self.bot.is_ready():
            return

        channel = self.bot.get_channel(self.TARGET_CHANNEL_ID)
        if not channel:
            return

        vc = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        
        # Voice එකට සම්බන්ධ වීම
        if not vc:
            try:
                vc = await channel.connect()
            except Exception as e:
                print(f"❌ Connection error: {e}")
                return

        # සින්දුවක් ප්ලේ වෙන්නේ නැත්නම් ඊළඟ එක ප්ලේ කරන්න
        if not vc.is_playing() and not vc.is_paused():
            song_url = self.playlist[self.current_index]
            
            try:
                # GitHub URL එක කෙලින්ම FFmpeg වලට ලබා දීම
                source = discord.FFmpegOpusAudio(song_url, **FFMPEG_OPTIONS)
                vc.play(source)
                
                print(f"🎵 ප්ලේ වෙනවා: Music {self.current_index + 1}")
                
                # ඊළඟ සින්දුවට මාරු වීම (Loop)
                self.current_index = (self.current_index + 1) % len(self.playlist)
                
            except Exception as e:
                print(f"❌ Playback error: {e}")
                # මොකක් හරි error එකක් ආවොත් තත්පර 10ක් ඉඳලා ඊළඟ සින්දුවට යන්න
                await asyncio.sleep(10)
                self.current_index = (self.current_index + 1) % len(self.playlist)

    @auto_play_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Music(bot))
