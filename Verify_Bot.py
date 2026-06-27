import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import datetime

# --- CONFIGURATION ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
THEME_COLOR = discord.Color.blue()
FOOTER_TEXT = "Developed By Clouskee"

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout is None so the button persists across bot restarts

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="clouskee_verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = interaction.client.db
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        # Fetch the server's configured verify role
        async with db.execute("SELECT verify_role_id FROM server_config WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()

        if not row or not row[0]:
            return await interaction.response.send_message("❌ The verification role has not been set up by the server owner.", ephemeral=True)

        role = interaction.guild.get_role(row[0])
        if not role:
            return await interaction.response.send_message("❌ The configured verification role no longer exists.", ephemeral=True)

        if role in interaction.user.roles:
            return await interaction.response.send_message("✅ You are already verified!", ephemeral=True)

        # Assign Role
        try:
            await interaction.user.add_roles(role)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I do not have permission to assign the verification role. Please check my hierarchy.", ephemeral=True)

        # Save Details to Database
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = str(interaction.user)
        
        await db.execute(
            "INSERT OR REPLACE INTO verifications (guild_id, user_id, username, verified_at) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, username, now)
        )
        await db.commit()

        # Success Message
        embed = discord.Embed(
            title="✨ Verification Successful!",
            description=(
                "Thank you for verifying your account. Your access has been granted, and the community channels are now unlocked!\n\n"
                "**What's next?**\n\n"
                "💬 Connect with others in our Global Chat & Chill VCs.\n"
                "🛠️ Get technical assistance in our Support Channels.\n"
                "📢 Stay updated on network status and service drops.\n\n"
                "Welcome aboard, and thank you for choosing Clouskee!"
            ),
            color=THEME_COLOR
        )
        embed.set_footer(text=FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ClouskeeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Required to fetch user avatars and roles reliably
        super().__init__(command_prefix="!", intents=intents)
        self.db = None

    async def setup_hook(self):
        # Initialize SQLite Database for Multi-Server Support
        self.db = await aiosqlite.connect("clouskee_database.db")
        
        await self.db.execute('''CREATE TABLE IF NOT EXISTS server_config (
            guild_id INTEGER PRIMARY KEY,
            verify_channel_id INTEGER,
            verify_role_id INTEGER
        )''')
        await self.db.execute('''CREATE TABLE IF NOT EXISTS trusted_users (
            guild_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (guild_id, user_id)
        )''')
        await self.db.execute('''CREATE TABLE IF NOT EXISTS verifications (
            guild_id INTEGER,
            user_id INTEGER,
            username TEXT,
            verified_at TEXT,
            PRIMARY KEY (guild_id, user_id)
        )''')
        await self.db.commit()

        # Register the persistent view
        self.add_view(VerifyView())
        
        # Sync slash commands globally
        await self.tree.sync()

bot = ClouskeeBot()

# --- ACCESS SECURITY CHECK ---
async def is_trusted(interaction: discord.Interaction) -> bool:
    """Checks if the user is the Guild Owner or on the Trusted list."""
    if interaction.user.id == interaction.guild.owner_id:
        return True
    
    async with interaction.client.db.execute(
        "SELECT 1 FROM trusted_users WHERE guild_id = ? AND user_id = ?", 
        (interaction.guild.id, interaction.user.id)
    ) as cursor:
        if await cursor.fetchone():
            return True

    await interaction.response.send_message("❌ Access Denied: Only the Server Owner and Trusted Users can use this command.", ephemeral=True)
    return False

# --- SLASH COMMANDS ---

@bot.tree.command(name="set_verify_channel", description="Sets the channel and deploys the Clouskee verification embed.")
@app_commands.check(is_trusted)
async def set_verify_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.client.db.execute(
        "INSERT INTO server_config (guild_id, verify_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET verify_channel_id=?",
        (interaction.guild.id, channel.id, channel.id)
    )
    await interaction.client.db.commit()

    embed = discord.Embed(
        title="Welcome to Clouskee",
        description=(
            "Welcome to the official Clouskee Discord Server!\n"
            "Your premier destination for high-performance VPNs, VPS deployment, Discord Bot hosting, and premium Game Servers.\n\n"
            "To unlock full access to our community, open support tickets, and manage your services, please click the Verify button below and complete the brief verification process.\n\n"
            "🚀 Let's build something great together!"
        ),
        color=THEME_COLOR
    )
    embed.set_footer(text=FOOTER_TEXT)
    
    await channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message(f"✅ Verification panel successfully deployed to {channel.mention}.", ephemeral=True)


@bot.tree.command(name="set_verify_role", description="Sets the role given to users upon successful verification.")
@app_commands.check(is_trusted)
async def set_verify_role(interaction: discord.Interaction, role: discord.Role):
    await interaction.client.db.execute(
        "INSERT INTO server_config (guild_id, verify_role_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET verify_role_id=?",
        (interaction.guild.id, role.id, role.id)
    )
    await interaction.client.db.commit()
    
    embed = discord.Embed(title="⚙️ Settings Updated", description=f"Verification role set to {role.mention}", color=THEME_COLOR)
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="trust", description="Grants bot configuration access to a user.")
async def trust(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("❌ Only the Server Owner can add trusted users.", ephemeral=True)

    await interaction.client.db.execute(
        "INSERT OR IGNORE INTO trusted_users (guild_id, user_id) VALUES (?, ?)",
        (interaction.guild.id, user.id)
    )
    await interaction.client.db.commit()
    
    embed = discord.Embed(title="🔒 Access Granted", description=f"{user.mention} has been added to the trusted list.", color=THEME_COLOR)
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="untrust", description="Revokes bot configuration access from a user.")
async def untrust(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("❌ Only the Server Owner can remove trusted users.", ephemeral=True)

    await interaction.client.db.execute(
        "DELETE FROM trusted_users WHERE guild_id = ? AND user_id = ?",
        (interaction.guild.id, user.id)
    )
    await interaction.client.db.commit()
    
    embed = discord.Embed(title="🔒 Access Revoked", description=f"{user.mention} has been removed from the trusted list.", color=THEME_COLOR)
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="trustlist", description="Displays all users with bot configuration access.")
@app_commands.check(is_trusted)
async def trustlist(interaction: discord.Interaction):
    async with interaction.client.db.execute("SELECT user_id FROM trusted_users WHERE guild_id = ?", (interaction.guild.id,)) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        description = "No trusted users added yet."
    else:
        description = "\n".join([f"<@{row[0]}> (ID: {row[0]})" for row in rows])

    embed = discord.Embed(title="🛡️ Trusted Users List", description=description, color=THEME_COLOR)
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="get_verifylist", description="Displays the 5 most recently verified users with their saved details.")
@app_commands.check(is_trusted)
async def get_verifylist(interaction: discord.Interaction):
    async with interaction.client.db.execute(
        "SELECT user_id, username, verified_at FROM verifications WHERE guild_id = ? ORDER BY verified_at DESC LIMIT 5", 
        (interaction.guild.id,)
    ) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        return await interaction.response.send_message("No users have verified yet.", ephemeral=True)

    # Defer response to handle multiple embeds
    await interaction.response.defer(ephemeral=True)

    embeds = []
    for row in rows:
        user_id, username, verified_at = row
        member = interaction.guild.get_member(user_id)
        
        embed = discord.Embed(color=THEME_COLOR)
        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="User ID", value=str(user_id), inline=True)
        embed.add_field(name="Verified Date", value=verified_at, inline=False)
        embed.set_footer(text=FOOTER_TEXT)
        
        # Attach the avatar if the member is still in the server
        if member and member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        embeds.append(embed)

    await interaction.followup.send(content="**Latest Verified Users:**", embeds=embeds)


@bot.tree.command(name="bot_commands", description="Lists all available Clouskee Bot commands.")
async def bot_commands(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Clouskee Bot Commands",
        description="Here is the list of available commands. Note that setup commands require Owner or Trusted permissions.",
        color=THEME_COLOR
    )
    
    commands_list = """
    `/set_verify_channel [channel]` - Deploys the verification panel.
    `/set_verify_role [role]` - Sets the role given upon verification.
    `/trust [user]` - Gives a user bot config access *(Owner Only)*.
    `/untrust [user]` - Revokes bot config access *(Owner Only)*.
    `/trustlist` - Shows all trusted managers.
    `/get_verifylist` - Shows recently verified users and avatars.
    `/bot_commands` - Displays this help message.
    """
    
    embed.add_field(name="Admin & Security Commands", value=commands_list, inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} - Clouskee Network Ready.")

# Run the bot
bot.run(BOT_TOKEN)
