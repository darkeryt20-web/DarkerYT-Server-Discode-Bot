import asyncio
import datetime
import os
import discord
from discord.ext import commands, tasks
import asyncpg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
TOKEN = os.getenv("P_BOT_TOKEN")
DATABASE_URL = os.getenv("P_DB_URL")
GUILD_ID = 1507562779135971398

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
db_pool = None

CUSTOM_CATEGORY_ID = None
user_upload_states = {}

async def init_db():
    global db_pool, CUSTOM_CATEGORY_ID
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        
        async with db_pool.acquire() as conn:
            # 1. Bot Settings Table (To save category ID persistently across restarts)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            ''')

            # 2. Other Tables
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS server_stats (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    all_members INT,
                    all_bots INT,
                    online_members INT,
                    online_bots INT
                );
                
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id BIGINT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    category TEXT
                );
                
                CREATE TABLE IF NOT EXISTS members (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    global_name TEXT,
                    user_tag TEXT,
                    server_tag_emoji TEXT,
                    server_tag_name TEXT,
                    status TEXT,
                    custom_status TEXT,
                    avatar_url TEXT,
                    avatar_decoration_url TEXT,
                    banner_url TEXT,
                    banner_color TEXT,
                    joined_at TIMESTAMP,
                    roles TEXT
                );
                
                CREATE TABLE IF NOT EXISTS activities (
                    user_id BIGINT PRIMARY KEY,
                    activity_name TEXT,
                    activity_type TEXT,
                    start_time TIMESTAMP,
                    image_url TEXT
                );
                
                CREATE TABLE IF NOT EXISTS voice_status (
                    user_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    channel_name TEXT
                );

                CREATE TABLE IF NOT EXISTS profile_customizations (
                    user_id BIGINT PRIMARY KEY,
                    background_url TEXT,
                    audio_url TEXT,
                    custom_cursor_url TEXT,
                    description TEXT,
                    profile_widget TEXT DEFAULT 'Under Construction 🚧',
                    profile_opacity INT DEFAULT 100,
                    profile_blur INT DEFAULT 0,
                    background_effect TEXT,
                    username_effect TEXT,
                    location TEXT,
                    social_links TEXT,
                    use_discord_avatar BOOLEAN DEFAULT TRUE,
                    discord_avatar_decoration BOOLEAN DEFAULT TRUE
                );
            ''')

            # Load saved category ID from database
            row = await conn.fetchrow("SELECT value FROM bot_settings WHERE key = 'custom_category_id'")
            if row:
                CUSTOM_CATEGORY_ID = int(row['value'])
                print(f"Loaded saved Custom Category ID from DB: {CUSTOM_CATEGORY_ID}")

        print("Database tables initialized successfully!")
    except Exception as e:
        print(f"Database Initialization Error: {e}")

# --- UI COMPONENTS FOR SETUP & CONTROL PANEL ---

class SetupPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 Create Your Custom Channel", style=discord.ButtonStyle.success, custom_id="create_custom_channel_btn")
    async def create_channel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await handle_channel_creation(interaction.user, interaction.guild, interaction)

class OpacityBlurModal(discord.ui.Modal):
    def __init__(self, user_id: int):
        super().__init__(title="Profile Opacity & Blur Settings")
        self.user_id = user_id
        self.opacity_input = discord.ui.TextInput(label="Profile Opacity (0 - 100)", default="100", required=True)
        self.blur_input = discord.ui.TextInput(label="Profile Blur (px e.g. 20px)", default="0px", required=True)
        self.add_item(self.opacity_input)
        self.add_item(self.blur_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            opacity = int(self.opacity_input.value)
            blur_val = int(self.blur_input.value.replace("px", "").strip())
            async with db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO profile_customizations (user_id, profile_opacity, profile_blur)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO UPDATE SET profile_opacity = $2, profile_blur = $3
                ''', self.user_id, opacity, blur_val)
            await interaction.response.send_message(f"✅ Opacity set to {opacity}% and Blur set to {blur_val}px saved!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Please enter valid numbers for opacity and blur.", ephemeral=True)

class TextModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, field_name: str, user_id: int):
        super().__init__(title=title)
        self.field_name = field_name
        self.user_id = user_id
        self.input_field = discord.ui.TextInput(label=label[:45], style=discord.TextStyle.paragraph, required=False)
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.input_field.value
        async with db_pool.acquire() as conn:
            query = f'''
                INSERT INTO profile_customizations (user_id, {self.field_name})
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET {self.field_name} = $2
            '''
            await conn.execute(query, self.user_id, value)
        await interaction.response.send_message(f"✅ Updated **{self.field_name.replace('_', ' ').title()}** successfully!", ephemeral=True)

class SelectDropdown(discord.ui.Select):
    def __init__(self, placeholder: str, options_list: list, field_name: str, user_id: int):
        options = [discord.SelectOption(label=opt, value=opt) for opt in options_list]
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)
        self.field_name = field_name
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        selected_val = self.values[0]
        async with db_pool.acquire() as conn:
            query = f'''
                INSERT INTO profile_customizations (user_id, {self.field_name})
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET {self.field_name} = $2
            '''
            await conn.execute(query, self.user_id, selected_val)
        await interaction.response.send_message(f"✅ Set **{self.field_name.replace('_', ' ').title()}** to `{selected_val}`", ephemeral=True)

class ControlPanelView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

        self.add_item(SelectDropdown(
            placeholder="✨ Choose Background Effect...",
            options_list=["Aurora", "Snowflakes", "Rain", "Blurred Background", "Night Time", "Old TV"],
            field_name="background_effect",
            user_id=user_id
        ))

        self.add_item(SelectDropdown(
            placeholder="🔤 Choose Username Effect...",
            options_list=["None", "Typewriter", "Rainbow", "Fuzzy", "Shuffle", "Green Sparkles"],
            field_name="username_effect",
            user_id=user_id
        ))

    @discord.ui.button(label="🎥 Upload Background", style=discord.ButtonStyle.primary, row=2)
    async def upload_bg(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_upload_states[self.user_id] = "background"
        await interaction.response.send_message("📤 Send your **Background (Video/Photo)** file in this channel!", ephemeral=True)

    @discord.ui.button(label="🎵 Upload Audio", style=discord.ButtonStyle.primary, row=2)
    async def upload_audio(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_upload_states[self.user_id] = "audio"
        await interaction.response.send_message("📤 Send your **Audio** file in this channel!", ephemeral=True)

    @discord.ui.button(label="🖱️ Upload Cursor", style=discord.ButtonStyle.primary, row=2)
    async def upload_cursor(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_upload_states[self.user_id] = "cursor"
        await interaction.response.send_message("📤 Send your **Custom Cursor** image in this channel!", ephemeral=True)

    @discord.ui.button(label="👁️ Opacity & Blur", style=discord.ButtonStyle.secondary, row=3)
    async def edit_opacity_blur(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = OpacityBlurModal(self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📝 Description", style=discord.ButtonStyle.secondary, row=3)
    async def edit_desc(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TextModal(title="Edit Bio & Location", label="Description & Location", field_name="description", user_id=self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔗 Social Links", style=discord.ButtonStyle.success, row=3)
    async def edit_socials(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TextModal(title="Link Social Profiles", label="Social Link URL", field_name="social_links", user_id=self.user_id)
        await interaction.response.send_modal(modal)

# --- HELPER FUNCTION FOR CHANNEL CREATION ---

async def handle_channel_creation(user: discord.Member, guild: discord.Guild, interaction: discord.Interaction = None):
    global CUSTOM_CATEGORY_ID
    target_category = guild.get_channel(CUSTOM_CATEGORY_ID) if CUSTOM_CATEGORY_ID else None

    if not target_category:
        msg = "❌ Category not set yet! Ask an admin to run `/set_category`."
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        return

    existing_channel = discord.utils.get(target_category.text_channels, name=f"customize-{user.name}".lower())
    if existing_channel:
        msg = f"📍 You already have a custom channel: {existing_channel.mention}"
        if interaction:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel = await guild.create_text_channel(
        name=f"customize-{user.name}",
        category=target_category,
        overwrites=overwrites
    )

    embed = discord.Embed(
        title="🛠️ Profile Customization Dashboard",
        description="Use the buttons below or upload assets directly to customize your profile!",
        color=discord.Color.purple()
    )
    embed.add_field(name="🖼️ Assets Uploader", value="Click upload buttons for `Background`, `Audio`, or `Custom Cursor`.\n`Profile Avatar`: **Auto-Fetched**", inline=False)
    embed.add_field(name="⚙️ Profile Widget", value="**Under Construction 🚧**", inline=False)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    view = ControlPanelView(user.id)
    await channel.send(content=f"Welcome {user.mention}! This is your private customization channel.", embed=embed, view=view)
    
    if interaction:
        msg = f"✨ Your private channel is ready: {channel.mention}"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

# --- BOT COMMANDS ---

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    await init_db()
    
    bot.add_view(SetupPanelView())

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    bot.loop.create_task(sync_server_data())
    stats_loop.start()

@bot.tree.command(name="set_category", description="Set Category for Custom Channels")
@commands.has_permissions(administrator=True)
async def set_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    global CUSTOM_CATEGORY_ID
    CUSTOM_CATEGORY_ID = category.id
    
    # Save Category ID persistently in database
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO bot_settings (key, value) VALUES ('custom_category_id', $1)
            ON CONFLICT (key) DO UPDATE SET value = $1
        ''', str(category.id))

    await interaction.response.send_message(f"✅ Category set to: **{category.name}** and saved to Database!", ephemeral=True)

@bot.tree.command(name="set_channel", description="Create Setup Channel with Button inside Category")
@commands.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, category: discord.CategoryChannel = None):
    await interaction.response.defer(ephemeral=True)
    
    target_category = category or (interaction.guild.get_channel(CUSTOM_CATEGORY_ID) if CUSTOM_CATEGORY_ID else None)
    if not target_category:
        await interaction.followup.send("❌ Please set a Category first using `/set_category`!", ephemeral=True)
        return

    setup_channel = await interaction.guild.create_text_channel(
        name="profile-setup",
        category=target_category,
        overwrites={
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
    )

    embed = discord.Embed(
        title="🌟 Profile Customization Center",
        description="Click the button below to create your private customization channel!",
        color=discord.Color.blue()
    )
    await setup_channel.send(embed=embed, view=SetupPanelView())
    await interaction.followup.send(f"✅ Setup channel created: {setup_channel.mention}", ephemeral=True)

@bot.tree.command(name="customize", description="Open your private Profile Customization Channel")
async def customize(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await handle_channel_creation(interaction.user, interaction.guild, interaction)

# --- MESSAGE UPLOAD HANDLER FOR BUTTONS ---

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if message.channel.name.startswith("customize-") and message.attachments:
        user_id = message.author.id
        current_state = user_upload_states.get(user_id)

        if not current_state:
            await message.channel.send("⚠️ Please click an upload button (Background, Audio, or Cursor) first before sending the file!")
            return

        attachment = message.attachments[0]
        url = attachment.url

        async with db_pool.acquire() as conn:
            if current_state == "background":
                await conn.execute('''
                    INSERT INTO profile_customizations (user_id, background_url)
                    VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET background_url = $2
                ''', user_id, url)
                await message.channel.send("📁 **Background asset successfully saved!**")
            elif current_state == "audio":
                await conn.execute('''
                    INSERT INTO profile_customizations (user_id, audio_url)
                    VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET audio_url = $2
                ''', user_id, url)
                await message.channel.send("🎵 **Audio asset successfully saved!**")
            elif current_state == "cursor":
                await conn.execute('''
                    INSERT INTO profile_customizations (user_id, custom_cursor_url)
                    VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET custom_cursor_url = $2
                ''', user_id, url)
                await message.channel.send("🖱️ **Custom cursor successfully saved!**")

        user_upload_states.pop(user_id, None)

    await bot.process_commands(message)

# --- TASKS & SYNCING ---

@tasks.loop(seconds=30)
async def stats_loop():
    guild = bot.get_guild(GUILD_ID)
    if not guild or not db_pool:
        return
    
    try:
        all_members = len([m for m in guild.members if not m.bot])
        all_bots = len([m for m in guild.members if m.bot])
        online_members = len([m for m in guild.members if not m.bot and m.status != discord.Status.offline])
        online_bots = len([m for m in guild.members if m.bot and m.status != discord.Status.offline])

        async with db_pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO server_stats (all_members, all_bots, online_members, online_bots) VALUES ($1, $2, $3, $4)',
                all_members, all_bots, online_members, online_bots
            )
            await conn.execute('''
                WITH cte AS (
                    SELECT id FROM server_stats ORDER BY timestamp DESC OFFSET 20
                )
                DELETE FROM server_stats WHERE id IN (SELECT id FROM cte);
            ''')
    except Exception as e:
        print(f"Error in stats_loop: {e}")

@bot.event
async def on_presence_update(before, after):
    if after.guild.id != GUILD_ID or not db_pool:
        return

    member = after
    custom_status = None
    activity_name = None
    activity_type = None
    activity_start = None
    activity_image = None

    for activity in member.activities:
        if isinstance(activity, discord.CustomActivity):
            custom_status = activity.name
        else:
            activity_name = activity.name
            activity_type = str(activity.type)
            if hasattr(activity, 'start') and activity.start:
                activity_start = activity.start.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            if hasattr(activity, 'album_cover_url'):
                activity_image = activity.album_cover_url
            elif hasattr(activity, 'large_image_url'):
                activity_image = activity.large_image_url

    status = str(member.status)
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                'UPDATE members SET status = $1, custom_status = $2 WHERE user_id = $3',
                status, custom_status, member.id
            )
            
            if activity_name:
                await conn.execute(
                    '''
                    INSERT INTO activities (user_id, activity_name, activity_type, start_time, image_url)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id) DO UPDATE SET
                        activity_name = $2, activity_type = $3, start_time = $4, image_url = $5
                    ''',
                    member.id, activity_name, activity_type, activity_start, activity_image
                )
            else:
                await conn.execute('DELETE FROM activities WHERE user_id = $1', member.id)
    except Exception as e:
        print(f"Error in on_presence_update: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.guild.id != GUILD_ID or not db_pool:
        return

    try:
        async with db_pool.acquire() as conn:
            if after.channel is None:
                await conn.execute('DELETE FROM voice_status WHERE user_id = $1', member.id)
            else:
                await conn.execute(
                    '''
                    INSERT INTO voice_status (user_id, channel_id, channel_name) 
                    VALUES ($1, $2, $3) 
                    ON CONFLICT (user_id) DO UPDATE SET channel_id = $2, channel_name = $3
                    ''',
                    member.id, after.channel.id, after.channel.name
                )
    except Exception as e:
        print(f"Error in on_voice_state_update: {e}")

async def sync_server_data():
    if not db_pool:
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"Guild with ID {GUILD_ID} not found!")
        return

    print(f"Syncing initial data for server: {guild.name}...")

    try:
        async with db_pool.acquire() as conn:
            await conn.execute('DELETE FROM channels')
            for channel in guild.channels:
                category_name = channel.category.name if channel.category else "No Category"
                await conn.execute(
                    '''INSERT INTO channels (channel_id, name, type, category) 
                       VALUES ($1, $2, $3, $4) 
                       ON CONFLICT (channel_id) DO UPDATE SET name = $2, type = $3, category = $4''',
                    channel.id, channel.name, str(channel.type), category_name
                )

            await conn.execute('DELETE FROM voice_status')
            for vc in guild.voice_channels:
                for member in vc.members:
                    await conn.execute(
                        '''INSERT INTO voice_status (user_id, channel_id, channel_name) 
                           VALUES ($1, $2, $3) 
                           ON CONFLICT (user_id) DO UPDATE SET channel_id = $2, channel_name = $3''',
                        member.id, vc.id, vc.name
                    )

            for member in guild.members:
                custom_status = None
                activity_name = None
                activity_type = None
                activity_start = None
                activity_image = None

                for activity in member.activities:
                    if isinstance(activity, discord.CustomActivity):
                        custom_status = activity.name
                    else:
                        activity_name = activity.name
                        activity_type = str(activity.type)
                        if hasattr(activity, 'start') and activity.start:
                            activity_start = activity.start.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                        if hasattr(activity, 'album_cover_url'):
                            activity_image = activity.album_cover_url
                        elif hasattr(activity, 'large_image_url'):
                            activity_image = activity.large_image_url

                avatar_url = str(member.avatar.url) if member.avatar else str(member.default_avatar.url)
                avatar_decoration_url = str(member.avatar_decoration.url) if hasattr(member, 'avatar_decoration') and member.avatar_decoration else None

                banner_url = None
                banner_color = None
                try:
                    user_obj = await bot.fetch_user(member.id)
                    banner_url = str(user_obj.banner.url) if user_obj.banner else None
                    banner_color = str(user_obj.accent_color) if user_obj.accent_color else None
                    await asyncio.sleep(0.02)
                except Exception:
                    pass

                roles_str = ", ".join([f"{r.name} ({r.color})" for r in member.roles if r.name != "@everyone"])
                user_tag = f"{member.name}#{member.discriminator}" if hasattr(member, 'discriminator') and member.discriminator != '0' else member.name

                server_tag_emoji = None
                server_tag_name = None
                clan_obj = getattr(member, 'clan', None) or getattr(member, 'guild_profile', None)
                if clan_obj:
                    server_tag_emoji = str(getattr(clan_obj, 'badge', None) or getattr(clan_obj, 'emoji', ''))
                    server_tag_name = str(getattr(clan_obj, 'tag', None) or getattr(clan_obj, 'name', ''))

                joined_at = None
                if member.joined_at:
                    joined_at = member.joined_at.astimezone(datetime.timezone.utc).replace(tzinfo=None)

                await conn.execute(
                    '''
                    INSERT INTO members (user_id, username, global_name, user_tag, server_tag_emoji, server_tag_name, status, custom_status, avatar_url, avatar_decoration_url, banner_url, banner_color, joined_at, roles)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = $2, global_name = $3, user_tag = $4, server_tag_emoji = $5, server_tag_name = $6,
                        status = $7, custom_status = $8, avatar_url = $9, avatar_decoration_url = $10,
                        banner_url = $11, banner_color = $12, joined_at = $13, roles = $14
                    ''',
                    member.id, member.name, member.global_name, user_tag, server_tag_emoji, server_tag_name,
                    str(member.status), custom_status, avatar_url, avatar_decoration_url, banner_url, banner_color, joined_at, roles_str
                )

                if activity_name:
                    await conn.execute(
                        '''
                        INSERT INTO activities (user_id, activity_name, activity_type, start_time, image_url)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (user_id) DO UPDATE SET
                            activity_name = $2, activity_type = $3, start_time = $4, image_url = $5
                        ''',
                        member.id, activity_name, activity_type, activity_start, activity_image
                    )

        print("Initial server data synced successfully!")
    except Exception as e:
        print(f"Error during initial sync: {e}")

if __name__ == "__main__":
    while True:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"Bot disconnected due to network error: {e}. Reconnecting in 5 seconds...")
            import time
            time.sleep(5)
