import discord
from discord.ext import commands, tasks
import asyncio

# FFmpeg settings - Direct streaming සහ Auto-reconnect සඳහා
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TARGET_CHANNEL_ID = 1463845234239606985  # සින්දු ප්ලේ විය යුතු Voice Channel ID
        
        # ඔයා ලබාදුන් Catbox MP3 ලින්ක් ලැයිස්තුව
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

    @tasks.loop(seconds=10)
    async def auto_play_loop(self):
        """සින්දු ප්ලේ වෙනවාදැයි පරීක්ෂා කර ප්ලේ කරන ප්‍රධාන ලූපය"""
        if not self.bot.is_ready():
            return

        channel = self.bot.get_channel(self.TARGET_CHANNEL_ID)
        if not channel:
            return

        # Voice Client එක පරීක්ෂා කිරීම
        vc = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        
        # Voice එකට සම්බන්ධ වී නොමැති නම් සම්බන්ධ වීම
        if not vc:
            try:
                vc = await channel.connect()
                print(f"✅ Voice Channel එකට සම්බන්ධ වුණා: {channel.name}")
            except Exception as e:
                print(f"❌ Connection error: {e}")
                return

        # සින්දුවක් ප්ලේ වෙන්නේ නැත්නම් ඊළඟ එක ප්ලේ කරන්න
        if not vc.is_playing() and not vc.is_paused():
            song_url = self.playlist[self.current_index]
            
            try:
                # Direct MP3 Link එක FFmpeg හරහා ප්ලේ කිරීම
                # Docker පාවිච්චි කරන නිසා 'executable' පේළිය අවශ්‍ය නැත
                source = discord.FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS)
                
                vc.play(source)
                print(f"🎵 දැන් ප්ලේ වෙන්නේ: Song {self.current_index + 1}")
                
                # ඊළඟ සින්දුවට මාරු වීම (අවසානයට පස්සේ නැවත 0 ට)
                self.current_index = (self.current_index + 1) % len(self.playlist)
                
            except Exception as e:
                print(f"❌ Playback error at index {self.current_index}: {e}")
                # වැරැද්දක් ආවොත් තත්පර 5ක් ඉඳලා ඊළඟ සින්දුවට මාරු වෙන්න
                await asyncio.sleep(5)
                self.current_index = (self.current_index + 1) % len(self.playlist)

    @auto_play_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    # Admin කෙනෙකුට Radio එක නවත්වන්න අවශ්‍ය නම්
    @commands.command(name="stop_radio")
    @commands.has_permissions(administrator=True)
    async def stop_radio(self, ctx):
        self.auto_play_loop.stop()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        await ctx.send("📻 Radio system stopped.")

async def setup(bot):
    await bot.add_cog(Music(bot))
