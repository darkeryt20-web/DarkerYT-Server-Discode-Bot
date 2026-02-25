import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask
from datetime import datetime

# --- Health Check (Using Port 8001 for Koyeb/Docker compatibility) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Verification Bot is Live!", 200

def run_web():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8001)

# --- Verification Button Logic ---
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Button stays active after bot restart

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_member_btn_v1", emoji="🛡️")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Using the specific Role ID provided
        ROLE_ID = 1474052348824522854
        role = interaction.guild.get_role(ROLE_ID)
        
        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("❌ You are already verified!", ephemeral=True)
            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Success! You now have the **{role.name}** role.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ **Permission Denied:** Move my Bot Role HIGHER than the Member role in Server Settings!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: Role ID `{ROLE_ID}` not found in this server.", ephemeral=True)

# --- Bot Logic ---
class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Essential for giving roles
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self):
        # Register the persistent view
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f'🛡️ Verification Bot: {self.user} is online.')
        
        # Target Channel ID
        CHANNEL_ID = 1474076593382096906
        channel = self.get_channel(CHANNEL_ID)
        
        if channel:
            # --- Cleanup: Delete old bot messages to keep channel clean ---
            async for message in channel.history(limit=15):
                if message.author == self.user:
                    try:
                        await message.delete()
                    except:
                        pass

            # --- Create Verification Embed ---
            embed = discord.Embed(
                title="🛡️ Server Verification",
                description=(
                    "Welcome! To prevent bots and keep our community safe, we require all "
                    "members to verify before accessing the rest of the server.\n\n"
                    "**Instructions:**\nClick the button below to receive the **Verified** "
                    "role and unlock all channels."
                ),
                color=discord.Color.from_rgb(43, 45, 49) # Dark Sleek Color
            )
            embed.set_footer(text="Security System • Verified Role ID: 1474052348824522854")
            embed.set_thumbnail(url=self.user.display_avatar.url)
            
            await channel.send(embed=embed, view=VerifyView())
            print(f"✅ Fresh verification message sent to #{channel.name}")

async def main():
    # Start separate thread for health check
    threading.Thread(target=run_web, daemon=True).start()
    
    bot = VerificationBot()
    async with bot:
        # Use the specific Verification Token variable
        token = os.getenv('DISCORD_TOKEN_VERIFY')
        if token:
            await bot.start(token)
        else:
            print("❌ ERROR: DISCORD_TOKEN_VERIFY environment variable not found!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutting down...")
