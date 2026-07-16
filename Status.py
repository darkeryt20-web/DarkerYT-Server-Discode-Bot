import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
import psycopg2
from dotenv import load_dotenv

# .env file එක load කරගැනීම
load_dotenv()

TOKEN = os.getenv("S_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Intents සැකසීම
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

class StatusBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Database Table එක සෑදීම සහ අවශ්‍ය නම් අලුත් Columns එකතු කිරීම
        init_db()
        # Slash commands sync කිරීම
        await self.tree.sync()
        # පසුබිමින් ක්‍රියාත්මක වන Update Task එක ආරම්භ කිරීම
        self.update_status_loop.start()

    @tasks.loop(minutes=10)  # Discord rate limits මඟහැරීමට විනාඩි 10කට වරක් update වේ
    async def update_status_loop(self):
        for guild in self.guilds:
            await update_guild_status(guild)

    @update_status_loop.before_loop
    async def before_update_status_loop(self):
        await self.wait_until_ready()

bot = StatusBot()

# --- DATABASE FUNCTIONS ---

def get_db_connection():
    url = DATABASE_URL
    if url.startswith("DATABASE_URL="):
        url = url.replace("DATABASE_URL=", "", 1)
    return psycopg2.connect(url)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table එක නැත්නම් සාදයි
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_status_channels (
            guild_id BIGINT PRIMARY KEY,
            all_bots_vc BIGINT,
            all_members_vc BIGINT,
            online_bots_vc BIGINT,
            online_members_vc BIGINT,
            paid_users_vc BIGINT,
            verified_members_vc BIGINT
        );
    """)
    conn.commit()

    # අවශ්‍ය අලුත් columns නොමැති නම් ඒවා automatic එකතු කරයි
    try:
        cursor.execute("ALTER TABLE guild_status_channels ADD COLUMN IF NOT EXISTS verified_role_id BIGINT;")
        cursor.execute("ALTER TABLE guild_status_channels ADD COLUMN IF NOT EXISTS paid_users_count INT DEFAULT 0;")
        cursor.execute("ALTER TABLE guild_status_channels ADD COLUMN IF NOT EXISTS bot_vc BIGINT;") # Bot එක ඉන්න ඕන VC එක
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database Alter Error: {e}")

    cursor.close()
    conn.close()

def save_channel(guild_id: int, column_name: str, channel_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO guild_status_channels (guild_id, {column_name})
        VALUES (%s, %s)
        ON CONFLICT (guild_id) 
        DO UPDATE SET {column_name} = EXCLUDED.{column_name};
    """, (guild_id, channel_id))
    conn.commit()
    cursor.close()
    conn.close()

def save_verified_role(guild_id: int, role_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guild_status_channels (guild_id, verified_role_id)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) 
        DO UPDATE SET verified_role_id = EXCLUDED.verified_role_id;
    """, (guild_id, role_id))
    conn.commit()
    cursor.close()
    conn.close()

def save_paid_count(guild_id: int, count: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guild_status_channels (guild_id, paid_users_count)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) 
        DO UPDATE SET paid_users_count = EXCLUDED.paid_users_count;
    """, (guild_id, count))
    conn.commit()
    cursor.close()
    conn.close()

def get_guild_config(guild_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT all_bots_vc, all_members_vc, online_bots_vc, online_members_vc, 
               paid_users_vc, verified_members_vc, verified_role_id, paid_users_count, bot_vc
        FROM guild_status_channels WHERE guild_id = %s;
    """, (guild_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "all_bots_vc": row[0],
            "all_members_vc": row[1],
            "online_bots_vc": row[2],
            "online_members_vc": row[3],
            "paid_users_vc": row[4],
            "verified_members_vc": row[5],
            "verified_role_id": row[6],
            "paid_users_count": row[7] if row[7] is not None else 0,
            "bot_vc": row[8]
        }
    return None

# --- BOT VC JOIN HELPER ---
async def join_bot_to_vc(guild: discord.Guild):
    config = get_guild_config(guild.id)
    if not config or not config["bot_vc"]:
        return

    channel_id = config["bot_vc"]
    channel = guild.get_channel(channel_id)
    
    if channel and isinstance(channel, discord.VoiceChannel):
        voice_client = guild.voice_client
        try:
            if voice_client:
                # දැනටමත් වෙන VC එකක ඉන්නවා නම් අලුත් VC එකට move වෙනවා
                if voice_client.channel.id != channel.id:
                    await voice_client.move_to(channel)
            else:
                # මුලින්ම VC එකට join වෙනවා
                await channel.connect()
            print(f"[{guild.name}] Joined Voice Channel: {channel.name}")
        except Exception as e:
            print(f"Error joining VC in {guild.name}: {e}")

# --- HELPER UPDATE FUNCTION ---

async def update_guild_status(guild: discord.Guild):
    config = get_guild_config(guild.id)
    if not config:
        return

    # සාමාජිකයන් සහ Bot ගණන් බැලීම
    all_members = guild.member_count or len(guild.members)
    all_bots = len([m for m in guild.members if m.bot])
    online_members = len([m for m in guild.members if not m.bot and m.status != discord.Status.offline])
    online_bots = len([m for m in guild.members if m.bot and m.status != discord.Status.offline])
    
    # Paid Users Count
    paid_users = config["paid_users_count"]
    
    # Verified Members Count
    verified_members = 0
    verified_role_id = config["verified_role_id"]
    if verified_role_id:
        verified_members = len([m for m in guild.members if any(r.id == verified_role_id for r in m.roles)])

    # Channel Names
    updates = [
        (config["all_bots_vc"], f"🤖 ᴀʟʟ ʙᴏᴛѕ: {all_bots}"),
        (config["all_members_vc"], f"👥 ᴀʟʟ ᴍᴇᴍʙᴇʀ: {all_members}"),
        (config["online_bots_vc"], f"🟢 ᴏɴʟɪɴᴇ ʙᴏᴛѕ: {online_bots}"),
        (config["online_members_vc"], f"🔵 ᴏɴʟɪɴᴇ ᴍᴇᴍʙᴇʀ: {online_members}"),
        (config["paid_users_vc"], f"💎 ᴘᴀɪᴅ ᴜѕᴇʀѕ: {paid_users}"),
        (config["verified_members_vc"], f"🛡️ ᴠᴇʀɪꜰɪᴇᴅ ᴍᴇᴍʙᴇʀѕ: {verified_members}")
    ]

    for channel_id, new_name in updates:
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.VoiceChannel):
                try:
                    if channel.name != new_name:
                        await channel.edit(name=new_name)
                except discord.HTTPException as e:
                    print(f"Error updating channel {channel_id} in {guild.name}: {e}")

# --- OWNER ONLY CHECK ---
def is_server_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == interaction.guild.owner_id:
            return True
        await interaction.response.send_message(
            "❌ ඔබට මෙම Command එක භාවිත කිරීමට අවසර නැත! මෙය කළ හැක්කේ **Server Owner** ට පමණි.", 
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

# --- SLASH COMMANDS ---

class StatusGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="status", description="Manage Server Status voice channels")

    @app_commands.command(name="setup-ab", description="Sets the VC to display All Bots count")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def setup_ab(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "all_bots_vc", channel.id)
        await interaction.response.send_message(f"✅ All Bots VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    @app_commands.command(name="setup-am", description="Sets the VC to display All Members count")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def setup_am(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "all_members_vc", channel.id)
        await interaction.response.send_message(f"✅ All Members VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    @app_commands.command(name="setup-ob", description="Sets the VC to display Online Bots count")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def setup_ob(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "online_bots_vc", channel.id)
        await interaction.response.send_message(f"✅ Online Bots VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    @app_commands.command(name="setup-om", description="Sets the VC to display Online Members count")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def setup_om(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "online_members_vc", channel.id)
        await interaction.response.send_message(f"✅ Online Members VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    @app_commands.command(name="setup-pm", description="Sets the VC to display Paid Users Count")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def setup_pm(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "paid_users_vc", channel.id)
        await interaction.response.send_message(f"✅ Paid Users VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    @app_commands.command(name="setup-vm", description="Sets the VC to display Verified Members count")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def setup_vm(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "verified_members_vc", channel.id)
        await interaction.response.send_message(f"✅ Verified Members VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    @app_commands.command(name="update-now", description="Manually triggers the status update cycle across all channels immediately")
    @is_server_owner()
    async def update_now(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await update_guild_status(interaction.guild)
        await interaction.followup.send("🔄 සියලුම Status VC සාර්ථකව Update කරන ලදී!")

bot.tree.add_command(StatusGroup())

# --- SET CONFIGURATION SLASH GROUP ---

class SetGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="set", description="Set dynamic values for Status channels")

    # /set vc [channel]
    @app_commands.command(name="vc", description="Selects the Voice Channel for the Bot to join and stay")
    @app_commands.describe(channel="Select the Voice Channel")
    @is_server_owner()
    async def set_vc(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        save_channel(interaction.guild_id, "bot_vc", channel.id)
        await interaction.response.send_message(f"✅ Bot එක රැඳී සිටින VC එක ලෙස **{channel.name}** සාර්ථකව සැකසුවා! දැන් Bot එයට Join වේවි.", ephemeral=True)
        # වහාම VC එකට Join වීම
        await join_bot_to_vc(interaction.guild)

    # /set vr [role]
    @app_commands.command(name="vr", description="Sets the role used to count Verified Members")
    @app_commands.describe(role="Select the Verified Members Role")
    @is_server_owner()
    async def set_vr(self, interaction: discord.Interaction, role: discord.Role):
        save_verified_role(interaction.guild_id, role.id)
        await interaction.response.send_message(f"✅ Verified Role එක ලෙස **@{role.name}** සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

    # /set pm [count]
    @app_commands.command(name="pm", description="Sets the manual count for Paid Users")
    @app_commands.describe(count="Enter the number of Paid Users")
    @is_server_owner()
    async def set_pm(self, interaction: discord.Interaction, count: int):
        if count < 0:
            await interaction.response.send_message("❌ කරුණාකර 0 ට වඩා වැඩි අගයක් ඇතුළත් කරන්න.", ephemeral=True)
            return
        save_paid_count(interaction.guild_id, count)
        await interaction.response.send_message(f"✅ Paid Users ගණන **{count}** ලෙස සාර්ථකව සැකසුවා!", ephemeral=True)
        await update_guild_status(interaction.guild)

bot.tree.add_command(SetGroup())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print("------")
    
    # Bot Online වූ සැනින් Configure කර ඇති VC වලට Auto Join වීම
    for guild in bot.guilds:
        await join_bot_to_vc(guild)

bot.run(TOKEN)
