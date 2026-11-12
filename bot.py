import os
import asyncio
import discord
from discord.ext import commands
from aiohttp import web
from dotenv import load_dotenv

# Local එකේදී .env ගොනුව Read කරගැනීමට (Koyeb වලදී මෙය ස්වයංක්‍රීයව Environment Variables වලින් ලබා ගනී)
load_dotenv()

# .env එකෙන් හෝ Koyeb Settings වලින් Token එක ලබා ගැනීම
TOKEN = os.getenv("DISCORD_TOKEN")

# Bot Setup
intents = discord.Intents.default()
intents.members = True  # Server members බලා ගැනීමට අත්‍යවශ්‍යයි

bot = commands.Bot(command_prefix="!", intents=intents)

# ඔබේ Discord Server ID එක
GUILD_ID = 1507562779135971398 

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Discord Verification Bot is ready!")

# CORS Headers සමඟ සියලුම Responses සඳහා Headers එකතු කිරීමේ Middleware එක
@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        return web.Response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
    
    try:
        response = await handler(request)
    except web.HTTPException as ex:
        response = ex
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Web Server එක හරහා Frontend එකෙන් එන Request එක Check කිරීම
async def handle_verify(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return web.json_response({"success": False, "error": "Bot is not in the specified server."})
        
        # User Server එකේ ඉන්නවද බැලීම
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                member = None

        if member:
            return web.json_response({"success": True, "message": "User is in the server!"})
        else:
            return web.json_response({"success": False, "message": "User has not joined the server yet."})
            
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=400)

async def init_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_post('/verify-user', handle_verify)
    app.router.add_options('/verify-user', handle_verify)
    return app

async def main():
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Koyeb එකේදී Port එක අල්ලගැනීමට සකස් කිරීම
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await site.start()
    print(f"Verification Web Server running on http://0.0.0.0:{port}")
    
    if not TOKEN:
        print("Error: DISCORD_TOKEN is missing in environment variables!")
        return

    # මෙන්න මෙතැන දැන් .env එකෙන් එන Variable එක පාවිච්චි වේ
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
