import os
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

TOKEN = os.getenv("ACTIVITY_DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


def extract_active_activity(member: discord.Member):
    if not member or member.bot or not member.activities:
        return None

    chosen = None
    for act in member.activities:
        if act.type != discord.ActivityType.custom:
            chosen = act
            break

    if chosen is None:
        for act in member.activities:
            if getattr(act, "name", None) or getattr(act, "state", None) or getattr(act, "emoji", None):
                chosen = act
                break

    if chosen is None:
        return None

    large_image = None
    try:
        large_image = getattr(chosen, "large_image_url", None)
    except Exception:
        large_image = None

    emoji_str = None
    if getattr(chosen, "emoji", None):
        emoji_str = str(chosen.emoji)

    payload = {
        "type": chosen.type.name if hasattr(chosen.type, "name") else str(chosen.type),
        "name": getattr(chosen, "name", None),
        "details": getattr(chosen, "details", None),
        "state": getattr(chosen, "state", None),
        "emoji": emoji_str,
        "large_image": large_image,
    }

    if not any([payload["name"], payload["details"], payload["state"], payload["emoji"]]):
        return None

    return payload


def _update_supabase_activity_sync(discord_id: str, activity_data):
    if not supabase:
        raise RuntimeError("Supabase client is not initialized. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    return (
        supabase.table("profiles")
        .update({"discord_activity": activity_data})
        .eq("discord_id", discord_id)
        .execute()
    )


async def sync_member_discord_activity(member: discord.Member) -> bool:
    if not member or member.bot or not supabase:
        return False
    activity_data = extract_active_activity(member)
    await asyncio.to_thread(_update_supabase_activity_sync, str(member.id), activity_data)
    return True


class ClouskeeActivityBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        # {guild_id: {"db_channel_id": int, "db_msg_id": int, "vc_id": int}}
        self.configs = {}

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Activity Sync Bot Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Live Activity")
        )
        for guild in self.guilds:
            await self.ensure_vc_connection(guild)

    async def save_config_to_db(self, guild: discord.Guild):
        if not guild:
            return
        guild_id = guild.id
        config = self.configs.get(guild_id, {})
        db_channel_id = config.get("db_channel_id")
        if not db_channel_id:
            return

        db_channel = guild.get_channel(db_channel_id)
        if not db_channel:
            return

        payload = {
            "type": "ACTIVITY_BOT_CONFIG",
            "vc_id": config.get("vc_id")
        }
        content = f"```json\n{json.dumps(payload)}\n```"

        db_msg_id = config.get("db_msg_id")
        if db_msg_id:
            try:
                msg = await db_channel.fetch_message(db_msg_id)
                await msg.edit(content=content)
                return
            except discord.NotFound:
                pass

        new_msg = await db_channel.send(content)
        config["db_msg_id"] = new_msg.id

    async def ensure_vc_connection(self, guild: discord.Guild):
        config = self.configs.get(guild.id, {})
        vc_id = config.get("vc_id")
        if not vc_id:
            return

        vc_channel = guild.get_channel(vc_id)
        if not vc_channel or not isinstance(vc_channel, discord.VoiceChannel):
            return

        voice_client = guild.voice_client
        try:
            if voice_client is None:
                await vc_channel.connect(self_deaf=True)
            elif voice_client.channel.id != vc_id:
                await voice_client.move_to(vc_channel)
        except Exception as e:
            print(f"[VC Error] Activity Bot could not join VC: {e}")


bot = ClouskeeActivityBot()


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.bot:
        return
    if extract_active_activity(before) != extract_active_activity(after):
        try:
            await sync_member_discord_activity(after)
        except Exception as e:
            print(f"[Activity Sync Error] {after.id}: {e}")


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id == bot.user.id:
        guild = member.guild
        config = bot.configs.get(guild.id, {})
        target_vc_id = config.get("vc_id")
        if target_vc_id and (after.channel is None or after.channel.id != target_vc_id):
            await asyncio.sleep(2)
            await bot.ensure_vc_connection(guild)


# ==================== SLASH COMMANDS ====================

def is_server_owner(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id


set_group = app_commands.Group(name="set", description="Clouskee Activity Bot Configuration (Owner Only)")


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the Activity Bot")
@app_commands.describe(channel="Select the voice channel")
async def set_vc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    bot.configs.setdefault(interaction.guild.id, {})["vc_id"] = channel.id
    await bot.save_config_to_db(interaction.guild)
    await bot.ensure_vc_connection(interaction.guild)
    await interaction.followup.send(f"🔊 Joined {channel.mention}, saved to DB, and auto-reconnect is active!", ephemeral=True)


@set_group.command(name="db", description="Set the Database channel & restore Activity Bot config")
@app_commands.describe(channel="Select the private DB text channel")
async def set_db(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    guild_id = guild.id
    config = bot.configs.setdefault(guild_id, {})
    config["db_channel_id"] = channel.id

    latest_data = None
    latest_msg_id = None

    async for msg in channel.history(limit=None, oldest_first=True):
        if msg.author.id != bot.user.id:
            continue
        raw = msg.content.strip()
        if raw.startswith("```json") and raw.endswith("```"):
            raw = raw[7:-3].strip()
        try:
            parsed = json.loads(raw)
            if parsed.get("type") == "ACTIVITY_BOT_CONFIG":
                latest_data = parsed
                latest_msg_id = msg.id
        except json.JSONDecodeError:
            continue

    if latest_data:
        if latest_data.get("vc_id"):
            config["vc_id"] = latest_data["vc_id"]
        config["db_msg_id"] = latest_msg_id
        await bot.ensure_vc_connection(guild)
        await interaction.followup.send(
            f"✅ **Activity Bot Database Restored from {channel.mention}!**\n"
            f"• **Voice Channel:** `{config.get('vc_id') or 'Not set'}`",
            ephemeral=True
        )
    else:
        await bot.save_config_to_db(guild)
        await interaction.followup.send(
            f"✅ **Activity Bot Database Initialized in {channel.mention}!**",
            ephemeral=True
        )


@bot.tree.command(name="syncactivity", description="Sync a member's current Discord activity to Supabase")
@app_commands.describe(member="Select a member (defaults to yourself)")
async def sync_activity_cmd(interaction: discord.Interaction, member: discord.Member = None):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    target = member or interaction.user

    try:
        synced = await sync_member_discord_activity(target)
        if not synced:
            return await interaction.followup.send("⚠️ Could not sync (bot user or Supabase not configured).", ephemeral=True)
        activity_preview = extract_active_activity(target)
        await interaction.followup.send(
            f"✅ Synced activity for {target.mention} to Supabase.\n```json\n{json.dumps(activity_preview, indent=2)}\n```",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Supabase sync failed: `{e}`", ephemeral=True)


bot.tree.add_command(set_group)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("ACTIVITY_DISCORD_TOKEN or DISCORD_TOKEN environment variable not found!")
    if not supabase:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required!")
    bot.run(TOKEN)
