import os
import datetime
import discord
import psycopg2
from discord.ext import commands
from discord.ui import Button, View, Select
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('V_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Configure Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True  # Required for VC joining

# --- Database Setup (PostgreSQL) ---

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is missing in .env file!")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Table for guild configurations updated with new roles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id BIGINT PRIMARY KEY,
            verify_channel_id BIGINT,
            voice_channel_id BIGINT,
            verify_role_id BIGINT,
            verify_message_id BIGINT,
            marketplace_role_id BIGINT,
            hostings_vpns_role_id BIGINT,
            software_zone_role_id BIGINT,
            chilling_gaming_role_id BIGINT,
            get_free_rewards_role_id BIGINT
        )
    ''')
    
    # Safely add columns if upgrading an existing database
    alter_queries = [
        "ALTER TABLE guild_config ADD COLUMN IF NOT EXISTS hostings_vpns_role_id BIGINT;",
        "ALTER TABLE guild_config ADD COLUMN IF NOT EXISTS software_zone_role_id BIGINT;",
        "ALTER TABLE guild_config ADD COLUMN IF NOT EXISTS chilling_gaming_role_id BIGINT;",
        "ALTER TABLE guild_config ADD COLUMN IF NOT EXISTS get_free_rewards_role_id BIGINT;"
    ]
    for q in alter_queries:
        try:
            cursor.execute(q)
        except:
            pass

    # Table for verifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            id SERIAL PRIMARY KEY,
            guild_id BIGINT,
            user_id BIGINT,
            username TEXT,
            global_name TEXT,
            avatar_url TEXT,
            join_position TEXT,
            joined_at TEXT,
            timestamp TEXT,
            interest TEXT,
            UNIQUE(guild_id, user_id)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# --- Animated Interest Emojis ---
ANIMATED_EMOJI_MENTIONS = {
    "marketplace": "<a:MarketPlace:1525719447854125196>",
    "hostings_vpns": "<a:Hostings_VPNs:1525719972683317308>",
    "software_zone": "<a:Software_Zone:1525720592882597898>",
    "chilling_gaming": "<a:Chilling_Gaming:1525721015718514748>",
    "get_free_rewards": "<a:Get_Free_Rewards:1525721252898275451>",
    "explore_everything": "<a:Explore_Everything:1524465515484025015>",
}

ANIMATED_EMOJIS = {
    key: discord.PartialEmoji(name=mention.split(":")[1], id=int(mention.split(":")[2].rstrip(">")), animated=True)
    for key, mention in ANIMATED_EMOJI_MENTIONS.items()
}

DB_COLUMN_TO_CONFIG_IDX = {
    "marketplace_role_id": 4,
    "hostings_vpns_role_id": 5,
    "software_zone_role_id": 6,
    "chilling_gaming_role_id": 7,
    "get_free_rewards_role_id": 8,
}

# --- Interest Options Mapping ---
INTEREST_OPTIONS = {
    "marketplace": {
        "label": "MarketPlace",
        "short_label": "MarketPlace",
        "description": "Buy, sell, and trade",
        "db_column": "marketplace_role_id",
    },
    "hostings_vpns": {
        "label": "Hostings & VPNs",
        "short_label": "Hostings & VPNs",
        "description": "Secure VPNs and reliable hosting",
        "db_column": "hostings_vpns_role_id",
    },
    "software_zone": {
        "label": "Software Zone",
        "short_label": "Software Zone",
        "description": "Premium software and apps",
        "db_column": "software_zone_role_id",
    },
    "chilling_gaming": {
        "label": "Chilling & Gaming",
        "short_label": "Chilling & Gaming",
        "description": "Hang out and play games",
        "db_column": "chilling_gaming_role_id",
    },
    "get_free_rewards": {
        "label": "Get Free Rewards",
        "short_label": "Get Free Rewards",
        "description": "Claim your free drops and rewards",
        "db_column": "get_free_rewards_role_id",
    },
    "explore_everything": {
        "label": "Explore Everything (All of the above)",
        "short_label": "Explore Everything",
        "description": "All of the above",
        "db_column": None,
    },
}

def format_interest_options_embed() -> str:
    lines = []
    for key in ("marketplace", "hostings_vpns", "software_zone", "chilling_gaming", "get_free_rewards", "explore_everything"):
        info = INTEREST_OPTIONS[key]
        lines.append(f"{ANIMATED_EMOJI_MENTIONS[key]} {info['label']}")
    return "\n".join(lines)


def format_stored_interests_display(interest: str) -> str:
    if not interest or interest == "N/A":
        return "N/A"
    label_to_key = {info["short_label"]: key for key, info in INTEREST_OPTIONS.items()}
    lines = []
    for part in [p.strip() for p in interest.split(",")]:
        key = label_to_key.get(part)
        if key:
            lines.append(f"{ANIMATED_EMOJI_MENTIONS[key]} {part}")
        else:
            lines.append(part)
    return "\n".join(lines)


def get_ordinal_suffix(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    match n % 10:
        case 1: return f"{n}st"
        case 2: return f"{n}nd"
        case 3: return f"{n}rd"
        case _: return f"{n}th"


async def calculate_join_position(member: discord.Member) -> str:
    try:
        members = [m for m in member.guild.members if m.joined_at is not None]
        members.sort(key=lambda m: m.joined_at)
        pos = members.index(member) + 1
        return f"{get_ordinal_suffix(pos)} Member to join"
    except Exception:
        return "Unknown Position"


def collect_interest_roles(guild, config, selected_values):
    roles = []
    seen_ids = set()

    def add_role(role):
        if role and role.id not in seen_ids:
            seen_ids.add(role.id)
            roles.append(role)

    if "explore_everything" in selected_values:
        for idx in (4, 5, 6, 7, 8):
            if config and config[idx]:
                add_role(guild.get_role(config[idx]))
    else:
        for value in selected_values:
            option_info = INTEREST_OPTIONS.get(value)
            if option_info and option_info["db_column"] and config:
                idx = DB_COLUMN_TO_CONFIG_IDX.get(option_info["db_column"])
                if idx is not None and config[idx]:
                    add_role(guild.get_role(config[idx]))
    return roles


def get_interest_labels_from_selection(selected_values):
    if "explore_everything" in selected_values:
        return [INTEREST_OPTIONS["explore_everything"]["short_label"]]
    return [
        INTEREST_OPTIONS[value]["short_label"]
        for value in selected_values
        if value in INTEREST_OPTIONS and value != "explore_everything"
    ]


async def assign_verification_roles(interaction, roles):
    if not roles:
        return True, []

    guild = interaction.guild
    member = interaction.user
    bot_member = guild.me
    roles_to_add = [role for role in roles if role not in member.roles]

    failed_roles = []
    for role in roles_to_add:
        if role >= bot_member.top_role:
            failed_roles.append(role)

    if failed_roles:
        return False, failed_roles

    try:
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="Clouskee Verification Process")
        return True, []
    except discord.Forbidden:
        return False, roles_to_add
    except discord.HTTPException:
        raise


# --- Database Helper Functions (PostgreSQL versions) ---
def get_guild_config(guild_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT verify_channel_id, voice_channel_id, verify_role_id, verify_message_id, 
               marketplace_role_id, hostings_vpns_role_id, software_zone_role_id, chilling_gaming_role_id, get_free_rewards_role_id
        FROM guild_config WHERE guild_id = %s
    ''', (guild_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def update_guild_config(guild_id, field, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO guild_config (guild_id) VALUES (%s) ON CONFLICT (guild_id) DO NOTHING', (guild_id,))
    cursor.execute(f'UPDATE guild_config SET {field} = %s WHERE guild_id = %s', (value, guild_id))
    conn.commit()
    cursor.close()
    conn.close()


def add_verification(guild_id, user_id, username, global_name, avatar_url, join_pos, joined_at, interest="N/A"):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    cursor.execute('''
        INSERT INTO verifications (guild_id, user_id, username, global_name, avatar_url, join_position, joined_at, timestamp, interest)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            username=excluded.username,
            global_name=excluded.global_name,
            avatar_url=excluded.avatar_url,
            join_position=excluded.join_position,
            joined_at=excluded.joined_at,
            timestamp=excluded.timestamp,
            interest=excluded.interest
    ''', (guild_id, user_id, username, global_name, avatar_url, join_pos, joined_at, timestamp, interest))
    conn.commit()
    cursor.close()
    conn.close()


def get_verification_count(guild_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM verifications WHERE guild_id = %s', (guild_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def get_user_verification(guild_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, global_name, avatar_url, join_position, joined_at, timestamp, interest 
        FROM verifications WHERE guild_id = %s AND user_id = %s
    ''', (guild_id, user_id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row if row else None


# --- UI Views ---

class InterestSelectView(View):
    def __init__(self):
        super().__init__(timeout=120)  

    @discord.ui.select(
        placeholder="Select your interest(s)...",
        custom_id="clouskee_interest_select",
        min_values=1,
        max_values=5,
        options=[
            discord.SelectOption(label="MarketPlace", value="marketplace", description="Buy, sell, and trade", emoji=ANIMATED_EMOJIS["marketplace"]),
            discord.SelectOption(label="Hostings & VPNs", value="hostings_vpns", description="Secure VPNs and reliable hosting", emoji=ANIMATED_EMOJIS["hostings_vpns"]),
            discord.SelectOption(label="Software Zone", value="software_zone", description="Premium software and apps", emoji=ANIMATED_EMOJIS["software_zone"]),
            discord.SelectOption(label="Chilling & Gaming", value="chilling_gaming", description="Hang out and play games", emoji=ANIMATED_EMOJIS["chilling_gaming"]),
            discord.SelectOption(label="Get Free Rewards", value="get_free_rewards", description="Claim your free drops and rewards", emoji=ANIMATED_EMOJIS["get_free_rewards"]),
            discord.SelectOption(label="Explore Everything", value="explore_everything", description="All of the above", emoji=ANIMATED_EMOJIS["explore_everything"]),
        ],
    )
    async def interest_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild_id = interaction.guild_id
        config = get_guild_config(guild_id)
        selected_values = select.values

        verify_role_id = config[2] if config else None
        roles_to_assign = []

        if verify_role_id:
            main_role = interaction.guild.get_role(verify_role_id)
            if main_role:
                roles_to_assign.append(main_role)

        roles_to_assign.extend(collect_interest_roles(interaction.guild, config, selected_values))

        if not roles_to_assign:
            embed = discord.Embed(
                title="**❌ Verification Failed**",
                description="The required **roles** have not been fully configured by the server owner yet.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        try:
            success, failed_roles = await assign_verification_roles(interaction, roles_to_assign)
            if not success:
                failed_names = ", ".join(f"**{role.name}**" for role in failed_roles)
                embed = discord.Embed(
                    title="**❌ Permission Error**",
                    description=(
                        "I couldn't assign one or more roles due to a **role hierarchy** issue.\n\n"
                        f"Failed role(s): {failed_names}\n\n"
                        "Please ask the server owner to move my bot role **above** these roles "
                        "in **Server Settings → Roles**, then try verifying again."
                    ),
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return

            interest_labels = get_interest_labels_from_selection(selected_values)
            joined_at_str = interaction.user.joined_at.isoformat(sep=' ', timespec='seconds') if interaction.user.joined_at else "N/A"
            join_pos_str = await calculate_join_position(interaction.user)

            add_verification(
                guild_id=guild_id,
                user_id=interaction.user.id,
                username=interaction.user.name,
                global_name=interaction.user.display_name,
                avatar_url=interaction.user.display_avatar.url,
                join_pos=join_pos_str,
                joined_at=joined_at_str,
                interest=", ".join(interest_labels)
            )

            embed = discord.Embed(
                title="**<a:Verified:1524455775202709665> Verification Successful!**",
                description=(
                    "Awesome! Your verification was successful. Welcome to the **Clouskee** family! 🚀\n\n"
                    "The server channels have been unlocked for you. Head over to the chat and say hi to the community!"
                ),
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)

        except discord.HTTPException as e:
            embed = discord.Embed(
                title="**❌ API Error**",
                description=f"An error occurred while verifying: **{e}**",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)


class VerificationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Verification", style=discord.ButtonStyle.green, custom_id="clouskee_persistent_verify_button")
    async def verify_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild_id
        config = get_guild_config(guild_id)

        if not config or not config[2]:
            embed = discord.Embed(
                title="**❌ Verification Failed**",
                description="The **verification role** has not been set up by the server owner yet.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        role = interaction.guild.get_role(config[2])
        if not role:
            embed = discord.Embed(
                title="**❌ Verification Failed**",
                description="The configured **verification role** no longer exists. Please contact an **admin**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if role in interaction.user.roles:
            embed = discord.Embed(
                title="**<a:Warning:1524455772803698858> Verification Status**",
                description=(
                    "Hey there! You have already been verified!\n"
                    "You already have full access to all the channels and services in the Clouskee server.\n\n"
                    "🚀 No further action is needed. Head back over to the chat channels and enjoy your stay!\n\n"
                    "<a:Warning:1524455772803698858> **Still having issues?**\n"
                    "Please open a **Support Ticket** in our support channel.\n"
                    "If you are unable to open a ticket, please send a direct message (DM) to <@1391883050035581148>.\n"
                ),
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="**👋 Welcome Aboard! | Complete Your Verification**",
            description=(
                "You are just one step away from joining **Clouskee**!\n"
                "To help us personalize your experience and unlock the right channels for you, "
                "please select what brings you to Clouskee today using the options below "
                "(you may choose up to **5** interests, or pick **Explore Everything** for all):\n\n"
                f"{format_interest_options_embed()}"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=InterestSelectView(), ephemeral=True)


# --- Bot Setup ---
class ClouskeeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerificationView())

    async def on_ready(self):
        print(f'Logged in as Bot ID: {self.user.id}')
        await self.tree.sync()  
        
        # Set Presence Status
        activity = discord.Activity(type=discord.ActivityType.playing, name="Protecting Clouskee | /verify")
        await self.change_presence(activity=activity)

        for guild in self.guilds:
            config = get_guild_config(guild.id)
            if config and config[1]:  
                vc = guild.get_channel(config[1])
                if vc and isinstance(vc, discord.VoiceChannel):
                    try:
                        await vc.connect()
                    except discord.ClientException:
                        pass  
                    except Exception as e:
                        print(f"Failed to connect to VC in {guild.name}: {e}")

        print('Clouskee Verification Bot is ready with Slash Commands!')

bot = ClouskeeBot()


# --- Role Persistence Handler ---
@bot.event
async def on_member_join(member: discord.Member):
    config = get_guild_config(member.guild.id)
    if not config:
        return

    record = get_user_verification(member.guild.id, member.id)
    if not record:
        return  

    interest_string = record[6]
    roles_to_reassign = []

    # Get Main Verified Role
    if config[2]:
        main_role = member.guild.get_role(config[2])
        if main_role:
            roles_to_reassign.append(main_role)

    # Decode short labels back into database selections
    if interest_string:
        selected_keys = []
        short_label_map = {info["short_label"]: key for key, info in INTEREST_OPTIONS.items()}
        for item in [i.strip() for i in interest_string.split(",")]:
            key = short_label_map.get(item)
            if key:
                selected_keys.append(key)
        
        roles_to_reassign.extend(collect_interest_roles(member.guild, config, selected_keys))

    if roles_to_reassign:
        bot_member = member.guild.me
        assignable = [r for r in roles_to_reassign if r < bot_member.top_role and r not in member.roles]
        if assignable:
            try:
                await member.add_roles(*assignable, reason="Clouskee Auto Role-Persistence Rejoin")
                print(f"[Persistence] Re-assigned {len(assignable)} roles to returning member {member.name} ({member.id})")
            except discord.Forbidden:
                print(f"[Persistence] Missing permissions to restore roles for {member.name}")
            except discord.HTTPException as e:
                print(f"[Persistence] HTTP Error restoring roles for {member.name}: {e}")


# --- Slash Command Ownership Verification Decorator ---
def is_guild_owner():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == interaction.guild.owner_id
    return app_commands.check(predicate)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        embed = discord.Embed(
            title="**❌ Access Denied**",
            description="Only the **Server Owner** can execute administrative commands.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="**❌ Error**",
            description=f"An unexpected tracking failure occurred: **{error}**",
            color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================================================================
# --- Administrative Control Commands ---
# ========================================================================

@bot.tree.command(name="set_verification_channel", description="Sets the channel where the verification embed message will be sent.")
@app_commands.describe(channel="The channel for verification")
@is_guild_owner()
async def set_verification_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="**<a:sheild:1525721252898275451> Welcome to Clouskee**",
        description=(
            "Welcome to the official **Clouskee** Discord Server! Your premier destination for "
            "high-performance **VPNs**, **VPS deployment**, **Discord Bot hosting**, and premium **Game Servers**.\n\n"
            "To unlock full access to our community, open **support tickets**, and manage your services, "
            "please click the **Start Verification** button below and complete the brief verification process. "
            "Let's build something great together!"
        ),
        color=discord.Color.brand_green()
    )
    embed.set_footer(text="Developed By Clouskee")
    view = VerificationView()

    try:
        msg = await channel.send(embed=embed, view=view)
    except discord.Forbidden:
        error_embed = discord.Embed(title="**❌ Error**", description="I don't have permission to send messages in that channel.", color=discord.Color.red())
        await interaction.followup.send(embed=error_embed)
        return

    update_guild_config(interaction.guild_id, 'verify_channel_id', channel.id)
    update_guild_config(interaction.guild_id, 'verify_message_id', msg.id)

    success_embed = discord.Embed(title="**✅ Success**", description=f"**Verification channel** has been set to {channel.mention} and the message has been posted.", color=discord.Color.green())
    await interaction.followup.send(embed=success_embed)


@bot.tree.command(name="set_vc", description="Sets the voice channel for the bot to join.")
@app_commands.describe(vc="The voice channel for the bot to join")
@is_guild_owner()
async def set_vc(interaction: discord.Interaction, vc: discord.VoiceChannel):
    update_guild_config(interaction.guild_id, 'voice_channel_id', vc.id)
    try:
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
        await vc.connect()
        embed = discord.Embed(title="**✅ Success**", description=f"Successfully set and joined the voice channel {vc.mention}.", color=discord.Color.green())
    except discord.Forbidden:
        embed = discord.Embed(title="**⚠️ Warning**", description=f"Saved {vc.mention} as the voice channel, but I **don't have permission** to join it.", color=discord.Color.orange())
    except Exception as e:
        embed = discord.Embed(title="**⚠️ Warning**", description=f"Saved {vc.mention} as the voice channel, but couldn't join: **{e}**", color=discord.Color.orange())

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="give_verification_count", description="Displays the total number of successfully verified users so far.")
@is_guild_owner()
async def give_verification_count(interaction: discord.Interaction):
    count = get_verification_count(interaction.guild_id)
    embed = discord.Embed(title="**📊 Verification Stats**", description=f"**Total Verified Users:** {count}", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="give_verification_details", description="Displays the extensive verified profile metrics for a specific member.")
@app_commands.describe(user_id_or_mention="Provide either a raw numeric User ID or a Direct User Mention (@user)")
@is_guild_owner()
async def give_verification_details(interaction: discord.Interaction, user_id_or_mention: str):
    clean_id = user_id_or_mention.replace("<@", "").replace(">", "").replace("!", "").strip()
    try:
        target_id = int(clean_id)
    except ValueError:
        embed = discord.Embed(title="**❌ Invalid Reference**", description="Could not map input to a numeric User ID profile.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    result = get_user_verification(interaction.guild_id, target_id)

    if result:
        username, global_name, avatar_url, join_position, joined_at, timestamp, interest = result
        formatted_interests = format_stored_interests_display(interest)

        embed = discord.Embed(title="**🔍 System Verification Profile**", color=discord.Color.blue())
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="👤 Target Identity", value=f"**Global Name:** {global_name}\n**Username:** @{username}\n**ID:** `{target_id}`", inline=False)
        embed.add_field(name="📈 Position & Server Metrics", value=f"**Join Position:** {join_position}\n**Server Joined:** {joined_at}", inline=True)
        embed.add_field(name="⏰ Verification Stamp", value=f"**Passed At:** {timestamp}", inline=True)
        embed.add_field(name="🏷️ Authenticated Interests", value=formatted_interests, inline=False)
    else:
        embed = discord.Embed(title="**🔍 Profile Missing**", description=f"No tracked database record matches user reference: `{target_id}`.", color=discord.Color.red())

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set_user_role", description="Force-assigns a target role to a member and updates their interest records.")
@app_commands.describe(member="The member to update", role="The role to grant")
@is_guild_owner()
async def set_user_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ This role ranks above my bot execution permissions.", ephemeral=True)
        return

    config = get_guild_config(interaction.guild_id)
    if not config:
        await interaction.response.send_message("❌ Server setup has not been initialized yet.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if role not in member.roles:
        await member.add_roles(role, reason="Force Admin Assign Override")

    matched_label = None
    for key, data in INTEREST_OPTIONS.items():
        if data["db_column"]:
            idx = DB_COLUMN_TO_CONFIG_IDX[data["db_column"]]
            if config[idx] == role.id:
                matched_label = data["short_label"]
                break

    record = get_user_verification(interaction.guild_id, member.id)
    current_interests = [i.strip() for i in record[6].split(",")] if (record and record[6] and record[6] != "N/A") else []

    if matched_label and matched_label not in current_interests:
        current_interests.append(matched_label)

    joined_str = member.joined_at.isoformat(sep=' ', timespec='seconds') if member.joined_at else "N/A"
    pos_str = await calculate_join_position(member)
    interest_payload = ", ".join(current_interests) if current_interests else "N/A"

    add_verification(
        guild_id=interaction.guild_id,
        user_id=member.id,
        username=member.name,
        global_name=member.display_name,
        avatar_url=member.display_avatar.url,
        join_pos=pos_str,
        joined_at=joined_str,
        interest=interest_payload
    )

    embed = discord.Embed(title="**✅ Role Granted Successfully**", description=f"Assigned {role.mention} to {member.mention} and updated logs.", color=discord.Color.green())
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="remove_user_role", description="Force-strips a specific role from a member and clears it from logs.")
@app_commands.describe(member="The member to update", role="The role to strip")
@is_guild_owner()
async def remove_user_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message("❌ Role ranks above execution permissions.", ephemeral=True)
        return

    config = get_guild_config(interaction.guild_id)
    if not config:
        await interaction.response.send_message("❌ Config missing.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if role in member.roles:
        await member.remove_roles(role, reason="Force Admin Strip Override")

    matched_label = None
    for key, data in INTEREST_OPTIONS.items():
        if data["db_column"]:
            idx = DB_COLUMN_TO_CONFIG_IDX[data["db_column"]]
            if config[idx] == role.id:
                matched_label = data["short_label"]
                break

    record = get_user_verification(interaction.guild_id, member.id)
    if record and record[6]:
        current_interests = [i.strip() for i in record[6].split(",")]
        if matched_label in current_interests:
            current_interests.remove(matched_label)
        
        interest_payload = ", ".join(current_interests) if current_interests else "N/A"
        joined_str = member.joined_at.isoformat(sep=' ', timespec='seconds') if member.joined_at else "N/A"
        pos_str = await calculate_join_position(member)

        add_verification(
            guild_id=interaction.guild_id,
            user_id=member.id,
            username=member.name,
            global_name=member.display_name,
            avatar_url=member.display_avatar.url,
            join_pos=pos_str,
            joined_at=joined_str,
            interest=interest_payload
        )

    embed = discord.Embed(title="**✅ Role Stripped Successfully**", description=f"Revoked {role.mention} from {member.mention}.", color=discord.Color.green())
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="check_roles_count", description="Compiles server authentication breakdowns and database distributions metrics.")
@is_guild_owner()
async def check_roles_count(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    config = get_guild_config(guild.id)
    total_verified = get_verification_count(guild.id)

    lines = []
    for key, info in INTEREST_OPTIONS.items():
        if not info["db_column"]:
            continue
        idx = DB_COLUMN_TO_CONFIG_IDX[info["db_column"]]
        role_id = config[idx] if config else None
        role = guild.get_role(role_id) if role_id else None
        
        count = len(role.members) if role else 0
        mention_string = role.mention if role else "`Not Configured`"
        lines.append(f"{ANIMATED_EMOJI_MENTIONS[key]} **{info['short_label']}:** {mention_string} | Total: `{count}`")

    embed = discord.Embed(title="**📊 Analytics & Allocation Breakdown**", color=discord.Color.purple())
    embed.add_field(name="Core Registry Metrics", value=f"🏆 **Total Verified via DB Log:** `{total_verified}` users", inline=False)
    embed.add_field(name="Interest Role Distributions", value="\n".join(lines), inline=False)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="set_role", description="Sets the main role assigned to users upon successful verification.")
@app_commands.describe(role="The role to assign")
@is_guild_owner()
async def set_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, 'verify_role_id', role.id)
    embed = discord.Embed(title="**✅ Success**", description=f"**Verification role** has been set to {role.mention}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set_marketplace_role", description="Sets the role for the MarketPlace interest.")
@app_commands.describe(role="The role for MarketPlace")
@is_guild_owner()
async def set_marketplace_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, 'marketplace_role_id', role.id)
    embed = discord.Embed(title="**✅ Success**", description=f"**MarketPlace** role has been set to {role.mention}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set_hostings_role", description="Sets the role for the Hostings & VPNs interest.")
@app_commands.describe(role="The role for Hostings & VPNs")
@is_guild_owner()
async def set_hostings_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, 'hostings_vpns_role_id', role.id)
    embed = discord.Embed(title="**✅ Success**", description=f"**Hostings & VPNs** role has been set to {role.mention}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set_software_role", description="Sets the role for the Software Zone interest.")
@app_commands.describe(role="The role for Software Zone")
@is_guild_owner()
async def set_software_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, 'software_zone_role_id', role.id)
    embed = discord.Embed(title="**✅ Success**", description=f"**Software Zone** role has been set to {role.mention}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set_chilling_role", description="Sets the role for the Chilling & Gaming interest.")
@app_commands.describe(role="The role for Chilling & Gaming")
@is_guild_owner()
async def set_chilling_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, 'chilling_gaming_role_id', role.id)
    embed = discord.Embed(title="**✅ Success**", description=f"**Chilling & Gaming** role has been set to {role.mention}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="set_rewards_role", description="Sets the role for the Get Free Rewards interest.")
@app_commands.describe(role="The role for Get Free Rewards")
@is_guild_owner()
async def set_rewards_role(interaction: discord.Interaction, role: discord.Role):
    update_guild_config(interaction.guild_id, 'get_free_rewards_role_id', role.id)
    embed = discord.Embed(title="**✅ Success**", description=f"**Get Free Rewards** role has been set to {role.mention}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN not found in .env!")
    elif not DATABASE_URL:
        print("CRITICAL ERROR: DATABASE_URL not found in .env!")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("CRITICAL ERROR: The token provided is invalid.")
        except Exception as e:
            print(f"Failed to start bot: {e}")
