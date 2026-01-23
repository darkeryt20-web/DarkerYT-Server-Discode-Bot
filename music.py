import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

# YouTube Download Options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

# FFmpeg Options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="YouTube එකෙන් සින්දු ප්ලේ කරන්න")
    async def play(self, interaction: discord.Interaction, music_name: str):
        await interaction.response.defer() # Response එකට වෙලාව ගන්න (Searching නිසා)

        # Member Voice channel එකක ඉන්නවාද බැලීම
        if not interaction.user.voice:
            return await interaction.followup.send("❌ ඔයා කලින් Voice Channel එකකට join වෙලා ඉන්න ඕනේ!")

        channel = interaction.user.voice.channel
        
        # Bot voice channel එකට සම්බන්ධ කිරීම
        if interaction.guild.voice_client is None:
            vc = await channel.connect()
        else:
            vc = interaction.guild.voice_client

        try:
            # YouTube Search
            info = await asyncio.to_thread(lambda: ytdl.extract_info(f"ytsearch:{music_name}", download=False)['entries'][0])
            url = info['url']
            title = info['title']

            # දැනට සින්දුවක් යයි නම් නතර කිරීම
            if vc.is_playing():
                vc.stop()

            # සින්දුව ප්ලේ කිරීම
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            vc.play(source)

            embed = discord.Embed(title="🎵 Now Playing", description=f"**{title}**", color=discord.Color.red())
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error එකක් ආවා: {e}")

    @app_commands.command(name="stop", description="සින්දුව නතර කර Bot ව ඉවත් කරන්න")
    async def stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("👋 මම ගියා! සින්දුව නතර කළා.")
        else:
            await interaction.response.send_message("❌ මම දැනටමත් Voice Channel එකක නැහැ.")

async def setup(bot):
    await bot.add_cog(Music(bot))
