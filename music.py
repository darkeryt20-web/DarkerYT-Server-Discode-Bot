import discord
from discord.ext import commands, tasks
import asyncio

# FFmpeg settings - Direct streaming සඳහා සකසා ඇත
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TARGET_CHANNEL_ID = 1463845234239606985 # සින්දු ප්ලේ විය යුතු Voice Channel ID
        
        # ඔයා ලබාදුන් Catbox MP3 Links ලැයිස්තුව
        self.playlist = [
            "https://files.catbox.moe/rab29r.mp3",
            "https://files.catbox.moe/j4bwbm.mp3",
            "https://files.catbox.moe/tgxy5b.mp3",
            "https://files.catbox.moe/2aemda.mp3",
            "https://files.catbox.moe/zr3mdq.mp3"
        ]
        
        self.current_index = 0
        self.auto_play_loop.start()

    def cog_unload(self):
        self.auto_play_loop.stop()

    @tasks.loop(seconds=5)
    async def auto_play_loop(self):
        """සින්දු ප්ලේ වෙනවාදැයි පරීක්ෂා කර ප්ලේ කරන ප්‍රධාන ලූපය"""
        if not self.bot.is_ready():
            return

        channel = self.bot.get_channel(self.TARGET_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Voice Channel (ID: {self.TARGET_CHANNEL_ID}) සොයාගත නොහැක!")
            return

        # Voice Client එක ලබා ගැනීම හෝ Connect වීම
        vc = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        
        if not vc:
            try:
                vc = await channel.connect()
                print(f"✅ Connected to: {channel.name}")
            except Exception as e:
                print(f"❌ Connection error: {e}")
                return

        # දැනට සින්දුවක් ප්ලේ වෙන්නේ නැත්නම් ඊළඟ එක ප්ලේ කරන්න
        if not vc.is_playing() and not vc.is_paused():
            song_url = self.playlist[self.current_index]
            
            try:
                # Direct MP3 Link එක FFmpeg හරහා ප්ලේ කිරීම
                source = discord.FFmpegOpusAudio(song_url, **FFMPEG_OPTIONS)
                vc.play(source)
                
                print(f"🎵 Now Playing: Song {self.current_index + 1}")
                
                # ඊළඟ සින්දුවට මාරු වීම (Loop back to 0 if at the end)
                self.current_index = (self.current_index + 1) % len(self.playlist)
                
            except Exception as e:
                print(f"❌ Playback error at index {self.current_index}: {e}")
                # Error එකක් ආවොත් ටිකක් වෙලා ඉඳලා ඊළඟ එකට මාරු වෙන්න
                await asyncio.sleep(5)
                self.current_index = (self.current_index + 1) % len(self.playlist)

    @auto_play_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    # Admin කෙනෙකුට අවශ්‍ය නම් Radio එක නතර කිරීමට command එකක්
    @commands.command(name="stop_radio")
    @commands.has_permissions(administrator=True)
    async def stop_radio(self, ctx):
        self.auto_play_loop.stop()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await ctx.send("📻 Radio stopped.")

async def setup(bot):
    await bot.add_cog(Music(bot))
