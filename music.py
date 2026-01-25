import discord
from discord.ext import commands, tasks

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.VC_ID = 1463845234239606985
        self.playlist = [
            "https://files.catbox.moe/rab29r.mp3",
            "https://files.catbox.moe/j4bwbm.mp3",
            "https://files.catbox.moe/tgxy5b.mp3",
            "https://files.catbox.moe/2aemda.mp3",
            "https://files.catbox.moe/zr3mdq.mp3"
        ]
        self.index = 0
        self.music_loop.start()

    @tasks.loop(seconds=15)
    async def music_loop(self):
        if not self.bot.is_ready(): return
        
        channel = self.bot.get_channel(self.VC_ID)
        if not channel: return

        # Check Voice Client
        vc = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        if not vc: 
            try:
                vc = await channel.connect()
                print(f"🎵 Connected to Music Channel: {channel.name}")
            except Exception as e:
                print(f"❌ Connection Error: {e}")
                return

        # Play Next Song if not playing
        if not vc.is_playing():
            try:
                source = discord.FFmpegPCMAudio(
                    self.playlist[self.index], 
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                    options="-vn"
                )
                vc.play(source)
                print(f"▶️ Now Playing Index: {self.index}")
                self.index = (self.index + 1) % len(self.playlist)
            except Exception as e:
                print(f"❌ Playback Error: {e}")

    @music_loop.before_loop
    async def before_music(self): 
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Music(bot))
