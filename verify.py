import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

# --- Global Data for Dashboard ---
verify_stats = {
    "name": "Verification Bot",
    "status": "Offline",
    "last_run": ""
}

# --- Verification Button Logic ---
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Me", style=discord.ButtonStyle.green, custom_id="verify_member_btn_v1", emoji="🛡️")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
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
                    await interaction.response.send_message("❌ **Permission Denied:** Move my Bot Role HIGHER than the Member role!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: Role ID `{ROLE_ID}` not found.", ephemeral=True)

# --- Bot Logic ---
class VerificationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())

    async def on_ready(self):
        # Update Dashboard Stats
        verify_stats["status"] = "Online"
        verify_stats["last_run"] = datetime.now().strftime("%I:%M %p")
        
        print(f'🛡️ Verification Bot: {self.user} is online.')
        
        CHANNEL_ID = 1474076593382096906
        channel = self.get_channel(CHANNEL_ID)
        
        if channel:
            async for message in channel.history(limit=15):
                if message.author == self.user:
                    try: await message.delete()
                    except: pass

            embed = discord.Embed(
                title="🛡️ Server Verification",
                description=(
                    "Welcome! To prevent bots and keep our community safe, we require all "
                    "members to verify before accessing the rest of the server.\n\n"
                    "**Instructions:**\nClick the button below to receive the **Verified** "
                    "role and unlock all channels."
                ),
                color=discord.Color.from_rgb(43, 45, 49)
            )
            embed.set_footer(text="Security System • Verified Role ID: 1474052348824522854")
            embed.set_thumbnail(url=self.user.display_avatar.url)
            
            await channel.send(embed=embed, view=VerifyView())
            print(f"✅ Fresh verification message sent to #{channel.name}")

async def start_verify_bot():
    bot = VerificationBot()
    async with bot:
        # Use DISCORD_TOKEN_VERIFY if you have a separate token, 
        # otherwise use the main DISCORD_TOKEN
        token = os.getenv('DISCORD_TOKEN_VERIFY') or os.getenv('DISCORD_TOKEN')
        if token:
            await bot.start(token)
        else:
            print("❌ ERROR: Verification Token not found!")

if __name__ == "__main__":
    try:
        asyncio.run(start_verify_bot())
    except KeyboardInterrupt:
        print("Bot shutting down...")
