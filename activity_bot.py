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


def _safe_url(obj, attr_name: str):
    try:
        val = getattr(obj, attr_name, None)
        return str(val) if val else None
    except Exception:
        return None


def serialize_single_activity(act) -> dict | None:
    if not act:
        return None

    act_type = act.type.name if hasattr(act.type, "name") else str(act.type)
    name = getattr(act, "name", None)
    details = getattr(act, "details", None)
    state = getattr(act, "state", None)
    emoji_str = str(getattr(act, "emoji")) if getattr(act, "emoji", None) else None

    # Extract images across Games/RPC, Spotify, and general activities
    large_image = (
        _safe_url(act, "large_image_url")
        or _safe_url(act, "album_cover_url")
    )
    small_image = _safe_url(act, "small_image_url")

    assets = getattr(act, "assets", None)
    raw_large_asset = None
    raw_small_asset = None
    if isinstance(assets, dict):
        raw_large_asset = assets.get("large_image")
        raw_small_asset = assets.get("small_image")
        if not large_image and isinstance(raw_large_asset, str) and raw_large_asset.startswith("http"):
            large_image = raw_large_asset
        if not small_image and isinstance(raw_small_asset, str) and raw_small_asset.startswith("http"):
            small_image = raw_small_asset

    timestamps = None
    if getattr(act, "timestamps", None):
        ts = act.timestamps
        if isinstance(ts, dict):
            timestamps = ts
        else:
            timestamps = {
                "start": getattr(ts, "get", lambda k: getattr(ts, k, None))("start") if hasattr(ts, "start") else None,
                "end": getattr(ts, "get", lambda k: getattr(ts, k, None))("end") if hasattr(ts, "end") else None,
            }

    item = {
        "type": act_type,
        "name": name,
        "details": details,
        "state": state,
        "emoji": emoji_str,
        "large_image": large_image,
        "small_image": small_image,
        "application_id": getattr(act, "application_id", None),
        "timestamps": timestamps,
    }

    if not any([item["name"], item["details"], item["state"], item["emoji"], item["large_image"], item["small_image"]]):
        return None

    return item


def build_activity_payload(member: discord.Member) -> dict | None:
    if not member or member.bot or not member.activities:
        return None

    all_activities = []
    for act in member.activities:
        parsed = serialize_single_activity(act)
        if parsed:
            all_activities.append(parsed)

    if not all_activities:
        return None

    # Primary activity: prefer non-custom activity (game/music/rpc), else first valid activity
    primary = None
    for act_item in all_activities:
        if act_item["type"] != "custom":
            primary = act_item
            break
    if primary is None:
        primary = all_activities[0]

    # Best available image across activities
    best_large_image = primary.get("large_image")
    best_small_image = primary.get("small_image")
    if not best_large_image:
        for act_item in all_activities:
            if act_item.get("large_image"):
                best_large_image = act_item["large_image"]
                break
    if not best_small_image:
        for act_item in all_activities:
            if act_item.get("small_image"):
                best_small_image = act_item["small_image"]
                break

    return {
        "type": primary["type"],
        "name": primary["name"],
        "details": primary["details"],
        "state": primary["state"],
        "emoji": primary["emoji"],
        "large_image": best_large_image,
        "small_image": best_small_image,
        "activities": all_activities,
    }


def _update_supabase_activity_sync(discord_id: str, activity_data: dict | None) -> int:
    if not supabase:
        raise RuntimeError("Supabase client is not initialized. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    res = (
        supabase.table("profiles")
        .update({"discord_activity": activity_data})
        .eq("discord_id", discord_id)
        .execute()
    )
    data = getattr(res, "data", None)
    return len(data) if isinstance(data, list) else 0


async def sync_member_discord_activity(member: discord.Member) -> tuple[bool, int, dict | None]:
    if not member or member.bot or not supabase:
        return False, 0, None
    activity_data = build_activity_payload(member)
    matched_rows = await asyncio.to_thread(_update_supabase_activity_sync, str(member.id), activity_data)
    return True, matched_rows, activity_data


class ClouskeeActivityBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}
        self._last_synced_json: dict[str, str] = {}

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


async def _handle_fast_presence_sync(member: discord.Member):
    uid = str(member.id)
    payload = build_activity_payload(member)
    encoded = json.dumps(payload, sort_keys=True)
    if bot._last_synced_json.get(uid) == encoded:
        return
    bot._last_synced_json[uid] = encoded
    try:
        _, matched, _ = await sync_member_discord_activity(member)
        print(f"[Activity Sync] user={uid} matched_rows={matched} has_activity={payload is not None}")
    except Exception as e:
        bot._last_synced_json.pop(uid, None)
        print(f"[Activity Sync Error] user={uid}: {e}")


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.bot:
        return
    asyncio.create_task(_handle_fast_presence_sync(after))


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


@bot.tree.command(name="syncactivity", description="Sync a member's current Discord activities & images to Supabase")
@app_commands.describe(member="Select a member (defaults to yourself)")
async def sync_activity_cmd(interaction: discord.Interaction, member: discord.Member = None):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    target = member or interaction.user

    try:
        synced, matched_rows, preview = await sync_member_discord_activity(target)
        if not synced:
            return await interaction.followup.send("⚠️ Could not sync (bot user or Supabase not configured).", ephemeral=True)
        bot._last_synced_json[str(target.id)] = json.dumps(preview, sort_keys=True)
        dumped = json.dumps(preview, indent=2)
        if len(dumped) > 1700:
            dumped = dumped[:1700] + "\n... (truncated)"
        await interaction.followup.send(
            f"✅ Synced `{target.id}` to Supabase (`matched_rows={matched_rows}`):\n```json\n{dumped}\n```",
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
