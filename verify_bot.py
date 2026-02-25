import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import asyncio
from datetime import datetime, timedelta

# --- Verification View (The Button Logic) ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None) # timeout=None makes the button permanent

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_button_sxd", emoji="🛡️")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_name = "Verified"  # Change this if your role name is different
        role = discord.utils.get(interaction.guild.roles, name=role_name)

        if role is None:
            await interaction.response.send_message(f"❌ Error: The `{role_name}` role was not found. Please contact an admin.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"🎉 Success! You now have the **{role_name}** role and full access.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to give you that role. Check my role hierarchy!", ephemeral=True)

# --- Bot Logic ---
class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Required to give roles
        intents.message_content = True
        super().__init__(command_prefix="?", intents=intents)

    async def on_ready(self):
        print(f'🛡️ {self.user} Verification Bot is online.')
        
        # This ensures the button works even after a bot restart
        self.add_view(VerifyView())
        
        CHANNEL_ID = 1474076593382096906
        channel = self.get_channel(CHANNEL_ID)

        if channel:
            # Clear old messages if you want a clean verification channel
            # await channel.purge(limit=5) 

            # Time Calculation (+4:30)
            adjusted_now = datetime.now() + timedelta(hours=4, minutes=30)
            current_time = adjusted_now.strftime("%I:%M %p")

            # --- Verification Embed ---
            embed = discord.Embed(
                title="🛡️ Server Verification",
                description=(
                    "Welcome! To prevent bots and keep our community safe, "
                    "we require all members to verify before accessing the rest of the server.\n\n"
                    "**Instructions:**\nClick the button below to receive the **Verified** role and unlock all channels."
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Security System Active • Initialized at {current_time}")
            
            # Send the message with the Button
            await channel.send(embed=embed, view=VerifyView())
            print(f"✅ Verification Button deployed to {channel.name}")

async def main():
    bot = VerificationBot()
    token = os.getenv('DISCORD_TOKEN_VERIFY')
    
    if token:
        async with bot:
            await bot.start(token)
    else:
        print("❌ CRITICAL: DISCORD_TOKEN_VERIFY is missing!")

if __name__ == "__main__":
    asyncio.run(main())
