import os
import re
import time
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()
TOKEN = os.getenv("SB_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Database Connection & Table Creation
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Warnings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Blocked text phrases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_texts (
            id SERIAL PRIMARY KEY,
            text_phrase TEXT UNIQUE,
            added_by BIGINT
        )
    ''')
    
    # 3. Allowed links (Whitelist) table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allowed_links (
            id SERIAL PRIMARY KEY
        )
    ''')
    
    # Check if 'domain_name' column exists in allowed_links, if not add it dynamically
    cursor.execute('''
        ALTER TABLE allowed_links 
        ADD COLUMN IF NOT EXISTS domain_name TEXT UNIQUE;
    ''')

    # Check if 'added_by' column exists in allowed_links, if not add it dynamically
    cursor.execute('''
        ALTER TABLE allowed_links 
        ADD COLUMN IF NOT EXISTS added_by BIGINT;
    ''')

    # 4. Bot Settings table (for Voice Channel and other dynamic configs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# In-memory history for spam tracking
user_history = {}

# --- STRICT LINK DETECTION REGEX ---
URL_PATTERN = re.compile(r'https?://[^\s]+', re.IGNORECASE)
DOMAIN_PATTERN = re.compile(r'\b(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+\b', re.IGNORECASE)

# Helper functions to fetch DB data
def get_blocked_phrases():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT text_phrase FROM blocked_texts")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0].lower() for row in rows]

def get_allowed_domains():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT domain_name FROM allowed_links WHERE domain_name IS NOT NULL")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    domains = [row[0].lower() for row in rows]
    domains.extend(["youtube.com", "youtu.be"])
    return domains

def get_saved_vc_id():
    """Fetches the saved Voice Channel ID from database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_settings WHERE key = 'voice_channel_id'")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return int(row[0]) if row else None
    except Exception as e:
        print(f"Error fetching VC ID: {e}")
        return None

@bot.event
async def on_ready():
    init_db()
    print(f'Logged in as {bot.user.name}')
    
    # Sync Commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} application (slash) command(s) successfully.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Dynamic Auto VC Connect on Startup
    saved_vc_id = get_saved_vc_id()
    if saved_vc_id:
        vc = bot.get_channel(saved_vc_id)
        if vc and isinstance(vc, discord.VoiceChannel):
            try:
                await vc.connect()
                print(f"Successfully auto-connected to saved VC: {vc.name}")
            except Exception as e:
                print(f"Could not connect to voice channel: {e}")
        else:
            print("Saved Voice Channel ID not found in this server.")
    else:
        print("No voice channel configured yet. Use `/set_vc` in a voice channel.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    current_time = time.time()
    content_lower = message.content.lower()

    # 1. Anti-Spam / Cooldown & Duplicate Check
    if user_id in user_history:
        last_time = user_history[user_id]['last_time']
        last_msg = user_history[user_id]['last_msg']

        if current_time - last_time < 2.0:
            await handle_violation(message, "Sending messages too fast (2s Cooldown)")
            return

        if content_lower == last_msg:
            await handle_violation(message, "Sending duplicate messages consecutively")
            return

    user_history[user_id] = {
        'last_msg': content_lower,
        'last_time': current_time
    }

    # 2. Strict Link Filtering
    found_urls = URL_PATTERN.findall(message.content)
    found_domains = DOMAIN_PATTERN.findall(message.content)
    all_links = list(set(found_urls + found_domains))

    if all_links:
        allowed_domains = get_allowed_domains()
        for link in all_links:
            clean_link = link.lower()
            clean_link = re.sub(r'^https?://', '', clean_link)
            clean_link = re.sub(r'^www\.', '', clean_link)
            clean_link = clean_link.split('/')[0]

            is_allowed = False
            for allowed in allowed_domains:
                if allowed == clean_link or clean_link.endswith("." + allowed):
                    is_allowed = True
                    break

            if not is_allowed:
                await handle_violation(message, f"Posting unauthorized links/text: {link}")
                return

    # 3. Dynamic Blocked Phrases Check
    blocked_phrases = get_blocked_phrases()
    for phrase in blocked_phrases:
        if phrase in content_lower:
            await handle_violation(message, f"Contains blocked text phrase: '{phrase}'")
            return

async def handle_violation(message, reason):
    try:
        await message.delete()
    except discord.Forbidden:
        pass

    # Log to Supabase
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO warnings (user_id, username, reason) VALUES (%s, %s, %s)",
            (message.author.id, str(message.author), reason)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

    # Send DM Warning
    try:
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            description=f"Your message in **{message.guild.name}** was deleted.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await message.author.send(embed=embed)
    except discord.Forbidden:
        pass

# ---------------------------------------------------------
# Slash Commands Section
# ---------------------------------------------------------

# NEW /set_vc Command
@bot.tree.command(name="set_vc", description="Set the default Voice Channel for the bot to auto-connect.")
async def set_vc(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ Oyata me command eka gahanna kalin Voice Channel ekakata join venna venava!", ephemeral=True)
        return

    voice_channel = interaction.user.voice.channel
    
    try:
        # Save to Supabase
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bot_settings (key, value) 
            VALUES ('voice_channel_id', %s) 
            ON CONFLICT (key) 
            DO UPDATE SET value = EXCLUDED.value
        ''', (str(voice_channel.id),))
        conn.commit()
        cursor.close()
        conn.close()

        # Connect to VC immediately
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        await interaction.response.send_message(f"✅ Auto-Join Voice Channel eka `{voice_channel.name}` (ID: {voice_channel.id}) vidiyata register kala!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Database error: {e}", ephemeral=True)

# /add_sb [text] command
@bot.tree.command(name="add_sb", description="Add text to the scam blocker list.")
@app_commands.describe(text="The phrase or characters to block")
async def add_sb(interaction: discord.Interaction, text: str):
    text_to_block = text.strip().lower()
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO blocked_texts (text_phrase, added_by) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (text_to_block, interaction.user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        await interaction.response.send_message(f"✅ Added `{text_to_block}` to the Scam Blocker list.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Database error: {e}", ephemeral=True)

# /allow_links [domain] command
@bot.tree.command(name="allow_links", description="Whitelist a domain to allow links from it.")
@app_commands.describe(domain="The website domain to allow (e.g., google.com, facebook.com)")
async def allow_links(interaction: discord.Interaction, domain: str):
    parsed = urlparse(domain if "://" in domain else f"http://{domain}")
    domain_to_allow = parsed.netloc.replace("www.", "").lower()
    if not domain_to_allow:
        domain_to_allow = domain.replace("www.", "").lower().strip()

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allowed_links (domain_name, added_by) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (domain_to_allow, interaction.user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        await interaction.response.send_message(f"✅ Whitelisted domain: `{domain_to_allow}`. Users can now share links from this website.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Database error: {e}", ephemeral=True)

bot.run(TOKEN)
