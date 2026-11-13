import asyncio
import os
from aiohttp import web
import discord
from discord.ext import commands

# 1. Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.command()
async def ping(ctx):
  await ctx.send("Pong! 🏓")


# 2. Setup Simple Web Server for Koyeb Health Check (Port 8000)
async def handle(request):
  return web.Response(text="Bot is running and healthy!")


async def run_web_server():
  app = web.Application()
  app.router.add_get("/", handle)
  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get("PORT", 8000))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()
  print(f"Web server started on port {port}")


async def main():
  # Run both the web server and the discord bot concurrently
  await run_web_server()
  await bot.start(os.environ.get("DISCORD_TOKEN"))


if __name__ == "__main__":
  asyncio.run(main())
