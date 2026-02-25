import discord
from discord.ext import commands
import os
import threading
import asyncio
from flask import Flask
from datetime import datetime

# --- Health Check (Using Port 8001 to avoid conflict with main.py) ---
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
        super().__init__(timeout=None) # Keeps button active after restart

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_member_btn", emoji="🛡️")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # EXACT role name from your request
        ROLE_NAME = "@Member" 
        role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
        
        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("❌ You are already verified!", ephemeral=True)
            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Success! You now have the **{ROLE_NAME}** role.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ I don't have permission to give that role. Check my role hierarchy!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: Role `{ROLE_NAME}` not found. Please create it!", ephemeral=True)

# --- Bot Logic ---
class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # Necessary to give roles
        intents.message_content = True
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self):
        # Register the view for persistence
        self.add_view(VerifyView())

    async def on_ready(self):
        print(f'🛡️ Verification Bot: {self.user} is online.')
        
        CHANNEL_ID = 1474076593382096906
        channel = self.get_channel(CHANNEL_ID)
        
        if channel:
            # --- Cleanup: Delete previous verification messages ---
            print("🧹 Cleaning up old verification messages...")
            async for message in channel.history(limit=20):
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
                    "**Instructions:**\nClick the button below to receive the **@Member** "
                    "role and unlock all channels."
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="Security System Powered by SXD")
            
            await channel.send(embed=embed, view=VerifyView())
            print(f"✅ Fresh verification message sent to {channel.name}")

async def main():
    # Start the Flask server for this bot on port 8001
    threading.Thread(target=run_web, daemon=True).start()
    
    bot = VerificationBot()
    async with bot:
        # Uses your new variable
        token = os.getenv('DISCORD_TOKEN_VERIFY')
        if token:
            await bot.start(token)
        else:
            print("❌ CRITICAL: DISCORD_TOKEN_VERIFY environment variable is missing!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Verification Bot shutting down.")
