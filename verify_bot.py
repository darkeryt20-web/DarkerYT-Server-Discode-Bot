import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask
from datetime import datetime

# --- Health Check (Using a different port 8001 for the 2nd bot) ---
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
        super().__init__(timeout=None) # Timeout=None makes the button persistent

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_button_sxd", emoji="🛡️")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_name = "Verified"
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        
        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("❌ You are already verified!", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Success! You now have the **{role_name}** role.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: Role '{role_name}' not found. Please contact an admin.", ephemeral=True)

# --- Bot Logic ---
class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Required to assign roles
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self):
        # This makes the button work even after the bot restarts
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f'🛡️ Verification Bot: {self.user} is online.')
        
        CHANNEL_ID = 1474076593382096906
        channel = self.get_channel(CHANNEL_ID)
        
        if channel:
            # --- Cleanup: Delete old bot messages to prevent double buttons ---
            async for message in channel.history(limit=50):
                if message.author == self.user:
                    try:
                        await message.delete()
                        print("🗑️ Deleted old verification message.")
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
                color=discord.Color.blue()
            )
            embed.set_footer(text="Security System Powered by SXD")
            embed.set_thumbnail(url=self.user.display_avatar.url)
            
            await channel.send(embed=embed, view=VerifyView())
            print(f"✅ Sent fresh verification message to {channel.name}")

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    bot = VerificationBot()
    async with bot:
        token = os.getenv('DISCORD_TOKEN_VERIFY')
        if token:
            await bot.start(token)
        else:
            print("❌ CRITICAL: DISCORD_TOKEN_VERIFY missing!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Verification Bot shutting down.")
