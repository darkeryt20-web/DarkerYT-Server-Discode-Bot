import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio

# YouTube & FFmpeg Options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TARGET_CHANNEL_ID = 1463845234239606985 # සින්දු යන Channel එක
        self.playlist = ["music1", "music2", "music3", "music4", "music5"] # ප්ලේ විය යුතු සින්දු
        self.current_index = 0
        self.is_looping = True
        
        # Auto-play ලූප් එක ආරම්භ කිරීම
        self.auto_play_loop.start()

    def cog_unload(self):
        self.auto_play_loop.stop()

    async def get_audio_url(self, search_query):
        """YouTube එකෙන් සින්දුව හොයාගෙන URL එක ලබා ගැනීම"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search_query}", download=False))
        if 'entries' in data:
            return data['entries'][0]['url'], data['entries'][0]['title']
        return None, None

    @tasks.loop(seconds=5)
    async def auto_play_loop(self):
        """සින්දු ප්ලේ වෙනවාදැයි පරීක්ෂා කර ප්ලේ කරන ලූප් එක"""
        if not self.bot.is_ready():
            return

        channel = self.bot.get_channel(self.TARGET_CHANNEL_ID)
        if not channel:
            return

        # Voice Client එක ලබා ගැනීම හෝ Connect වීම
        vc = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        
        if not vc:
            try:
                vc = await channel.connect()
            except Exception as e:
                print(f"❌ Voice connection error: {e}")
                return

        # දැනට සින්දුවක් ප්ලේ වෙන්නේ නැත්නම් ඊළඟ එක ප්ලේ කරන්න
        if not vc.is_playing() and not vc.is_paused():
            song_query = self.playlist[self.current_index]
            url, title = await self.get_audio_url(song_query)

            if url:
                try:
                    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                    vc.play(source)
                    print(f"🎵 Now Playing: {title}")
                    
                    # ඊළඟ සින්දුව සඳහා index එක මාරු කිරීම
                    self.current_index = (self.current_index + 1) % len(self.playlist)
                except Exception as e:
                    print(f"❌ Play error: {e}")

    @auto_play_loop.before_loop
    async def before_auto_play(self):
        await self.bot.wait_until_ready()

    # --- Manual Commands ---

    @commands.command(name="stop_radio")
    @commands.has_permissions(administrator=True)
    async def stop_radio(self, ctx):
        """දිගටම සින්දු යන එක නවත්වන්න (Admin Only)"""
        self.auto_play_loop.stop()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await ctx.send("📻 Radio system stopped.")

    @commands.command(name="start_radio")
    @commands.has_permissions(administrator=True)
    async def start_radio(self, ctx):
        """නැවතත් රේඩියෝ එක පණගන්වන්න"""
        if not self.auto_play_loop.is_running():
            self.auto_play_loop.start()
            await ctx.send("📻 Radio system started!")
        else:
            await ctx.send("📻 Radio is already running.")

async def setup(bot):
    await bot.add_cog(Music(bot))
