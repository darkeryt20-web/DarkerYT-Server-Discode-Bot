import discord
from discord.ext import commands
import asyncio

class MovieBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MOVIE_CH_ID = 1464902501567303712
        self.LOADING_GIF = "https://mir-s3-cdn-cf.behance.net/project_modules/hd/5eeea355389655.59822ff824b72.gif"
        
        # Movies List (ඔයාගේ links මෙතනට දාන්න)
        self.movies = {
            "The Great Flood": "https://files.catbox.moe/example1.mp4",
            "My Daughter is a Zombie": "https://files.catbox.moe/example2.mp4"
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

    @commands.command(name="movies")
    async def list_movies(self, ctx):
        if ctx.channel.id != self.MOVIE_CH_ID: return
        embed = discord.Embed(title="🎬 Available Movies", color=0xff0000)
        for movie in self.movies.keys():
            embed.add_field(name=movie, value="Status: ✅ Ready to Stream", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="start")
    async def start_movie(self, ctx, *, movie_name: str):
        if ctx.channel.id != self.MOVIE_CH_ID: return
        
        # Movie එක සෙවීම
        selected_url = None
        for name, url in self.movies.items():
            if movie_name.lower() in name.lower():
                selected_url = url
                movie_name = name
                break

        if not selected_url:
            return await ctx.send("❌ ඔය නමින් Movie එකක් නැහැ!")

        if not ctx.author.voice:
            return await ctx.send("❌ කලින් Voice Channel එකකට join වෙන්න!")

        # Loading Embed එක (ඔයා දුන්න GIF එක මෙතනට දානවා)
        loading_embed = discord.Embed(title=f"⏳ Loading {movie_name}...", color=0xffff00)
        loading_embed.set_image(url=self.LOADING_GIF)
        msg = await ctx.send(embed=loading_embed)

        # Voice එකට join වීම සහ Play කිරීම
        vc = ctx.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect()
        
        if vc.is_playing():
            vc.stop()

        try:
            source = discord.FFmpegPCMAudio(selected_url, **self.ffmpeg_options)
            vc.play(source)
            
            # ප්ලේ වෙන්න ගත්තම Embed එක Update කරනවා
            play_embed = discord.Embed(title="🎥 Now Playing", description=f"Streaming: **{movie_name}**", color=0x00ff00)
            play_embed.set_footer(text="Use .pause, .play or .stop to control")
            await msg.edit(embed=play_embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name="pause")
    async def pause(self, ctx):
        if ctx.voice_client: ctx.voice_client.pause()
        await ctx.send("⏸️ Movie Paused")

    @commands.command(name="play")
    async def resume(self, ctx):
        if ctx.voice_client: ctx.voice_client.resume()
        await ctx.send("▶️ Resuming...")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Streaming Stopped")

async def setup(bot):
    await bot.add_cog(MovieBot(bot))
