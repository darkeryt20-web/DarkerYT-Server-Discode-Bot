import os
import discord
from discord.ext import commands
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Get the bot token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Define bot intents (required for newer Discord.py versions)
intents = discord.Intents.default()
intents.message_content = True # Enable message content intent

# Create a bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Simple web server for health checks (Koyeb needs this for port 8000)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_health_check_server():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print("Health check server starting on port 8000...")
    httpd.serve_forever()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    # Start the health check server in a separate thread
    threading.Thread(target=run_health_check_server, daemon=True).start()

@bot.command(name='hello')
async def hello(ctx):
    """Responds with a simple hello message."""
    await ctx.send(f'Hello, {ctx.author.display_name}!')

@bot.command(name='ping')
async def ping(ctx):
    """Responds with the bot's latency."""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

if __name__ == '__main__':
    if TOKEN is None:
        print("Error: DISCORD_TOKEN environment variable not set.")
        exit(1)
    bot.run(TOKEN)
