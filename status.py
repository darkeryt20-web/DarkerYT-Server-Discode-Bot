import os
import re
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("STATS_TOKEN", os.getenv("STATUS_DISCORD_TOKEN"))

# Intents setup (Members & Presences intents are required for accurate online counts)
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


def replace_trailing_number(channel_name: str, new_count: int) -> str:
    """
    Keeps the exact emoji, font style, and prefix text intact,
    replacing only the number at the end of the channel name.
    """
    if re.search(r"\d+$", channel_name.strip()):
        return re.sub(r"\d+$", str(new_count), channel_name.strip())
    return f"{channel_name.strip()} {new_count}"


class ClouskeeStatsBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Stats Bot Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Server Stats 📊")
        )
        if not self.update_stats_loop.is_running():
            self.update_stats_loop.start()

        for guild in self.guilds:
            await self.ensure_vc_connection(guild)

    async def save_config_to_db(self, guild: discord.Guild):
        guild_id = guild.id
        config = self.configs.get(guild_id, {})
        db_channel_id = config.get("db_channel_id")
        if not db_channel_id:
            return

        db_channel = guild.get_channel(db_channel_id)
        if not db_channel:
            return

        payload = {
            "type": "STATS_CONFIG",
            "vc_id": config.get("vc_id"),
            "all_members_ch": config.get("all_members_ch"),
            "all_bots_ch": config.get("all_bots_ch"),
            "online_members_ch": config.get("online_members_ch"),
            "online_bots_ch": config.get("online_bots_ch"),
            "verified_members_ch": config.get("verified_members_ch"),
            "paid_users_ch": config.get("paid_users_ch"),
            "verified_role_id": config.get("verified_role_id"),
            "paid_role_id": config.get("paid_role_id")
        }

        config_msg_id = config.get("config_msg_id")
        content = f"```json\n{json.dumps(payload)}\n```"

        if config_msg_id:
            try:
                msg = await db_channel.fetch_message(config_msg_id)
                await msg.edit(content=content)
                return
            except discord.NotFound:
                pass

        new_msg = await db_channel.send(content)
        config["config_msg_id"] = new_msg.id

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
            print(f"[VC Error] Stats Bot could not join VC: {e}")

    async def update_guild_stats(self, guild: discord.Guild):
        config = self.configs.get(guild.id)
        if not config:
            return

        humans = [m for m in guild.members if not m.bot]
        bots = [m for m in guild.members if m.bot]

        all_members_count = len(humans)
        all_bots_count = len(bots)
        online_members_count = len([m for m in humans if m.status != discord.Status.offline])
        online_bots_count = len([m for m in bots if m.status != discord.Status.offline])

        verified_role = guild.get_role(config.get("verified_role_id")) if config.get("verified_role_id") else None
        paid_role = guild.get_role(config.get("paid_role_id")) if config.get("paid_role_id") else None

        verified_count = len(verified_role.members) if verified_role else 0
        paid_count = len(paid_role.members) if paid_role else 0

        updates = [
            (config.get("all_members_ch"), all_members_count),
            (config.get("all_bots_ch"), all_bots_count),
            (config.get("online_members_ch"), online_members_count),
            (config.get("online_bots_ch"), online_bots_count),
            (config.get("verified_members_ch"), verified_count),
            (config.get("paid_users_ch"), paid_count),
        ]

        for ch_id, count in updates:
            if not ch_id:
                continue
            channel = guild.get_channel(ch_id)
            if not channel:
                continue

            new_name = replace_trailing_number(channel.name, count)
            if channel.name != new_name:
                try:
                    await channel.edit(name=new_name, reason="Clouskee Auto Stats Update")
                    await asyncio.sleep(1.5)  # Prevent Discord rate limits
                except (discord.Forbidden, discord.HTTPException):
                    pass

    # Discord allows 2 channel renames per 10 minutes per channel; checking every 6 minutes is safe & responsive
    @tasks.loop(minutes=6)
    async def update_stats_loop(self):
        for guild in self.guilds:
            await self.update_guild_stats(guild)


bot = ClouskeeStatsBot()


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id == bot.user.id:
        guild = member.guild
        config = bot.configs.get(guild.id, {})
        target_vc_id = config.get("vc_id")

        if target_vc_id and (after.channel is None or after.channel.id != target_vc_id):
            await asyncio.sleep(2)
            await bot.ensure_vc_connection(guild)


# ==================== SLASH COMMANDS (OWNER ONLY) ====================

def is_server_owner(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id


set_group = app_commands.Group(name="set", description="Clouskee Server Status Configuration (Owner Only)")

all_sub = app_commands.Group(name="all", description="Set total counts channels", parent=set_group)
online_sub = app_commands.Group(name="online", description="Set online counts channels", parent=set_group)
verified_sub = app_commands.Group(name="verified", description="Set verified members channel & role", parent=set_group)
paid_sub = app_commands.Group(name="paid", description="Set paid users channel & role", parent=set_group)


async def handle_channel_set(interaction: discord.Interaction, key: str, label: str, channel: discord.VoiceChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})[key] = channel.id
    await bot.save_config_to_db(interaction.guild)
    await bot.update_guild_stats(interaction.guild)

    await interaction.followup.send(f"✅ **{label}** channel set to {channel.mention} and updated!", ephemeral=True)


@all_sub.command(name="members", description="Set the ALL MEMBER voice channel")
@app_commands.describe(channel="Select the voice channel")
async def set_all_members(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await handle_channel_set(interaction, "all_members_ch", "ALL MEMBER", channel)


@all_sub.command(name="bots", description="Set the ALL BOTS voice channel")
@app_commands.describe(channel="Select the voice channel")
async def set_all_bots(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await handle_channel_set(interaction, "all_bots_ch", "ALL BOTS", channel)


@online_sub.command(name="members", description="Set the ONLINE MEMBER voice channel")
@app_commands.describe(channel="Select the voice channel")
async def set_online_members(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await handle_channel_set(interaction, "online_members_ch", "ONLINE MEMBER", channel)


@online_sub.command(name="bots", description="Set the ONLINE BOTS voice channel")
@app_commands.describe(channel="Select the voice channel")
async def set_online_bots(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await handle_channel_set(interaction, "online_bots_ch", "ONLINE BOTS", channel)


@verified_sub.command(name="members", description="Set the VERIFIED MEMBERS voice channel")
@app_commands.describe(channel="Select the voice channel")
async def set_verified_members(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await handle_channel_set(interaction, "verified_members_ch", "VERIFIED MEMBERS", channel)


@verified_sub.command(name="role", description="Set the Verified Role to count")
@app_commands.describe(role="Select the verified role")
async def set_verified_role(interaction: discord.Interaction, role: discord.Role):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["verified_role_id"] = role.id
    await bot.save_config_to_db(interaction.guild)
    await bot.update_guild_stats(interaction.guild)

    await interaction.followup.send(f"✅ Verified role set to {role.mention} and synced!", ephemeral=True)


@paid_sub.command(name="users", description="Set the PAID USERS voice channel")
@app_commands.describe(channel="Select the voice channel")
async def set_paid_users(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await handle_channel_set(interaction, "paid_users_ch", "PAID USERS", channel)


@paid_sub.command(name="role", description="Set the Paid Users Role to count")
@app_commands.describe(role="Select the paid role")
async def set_paid_role(interaction: discord.Interaction, role: discord.Role):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["paid_role_id"] = role.id
    await bot.save_config_to_db(interaction.guild)
    await bot.update_guild_stats(interaction.guild)

    await interaction.followup.send(f"✅ Paid Users role set to {role.mention} and synced!", ephemeral=True)


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the Stats Bot")
@app_commands.describe(channel="Select the voice channel")
async def set_vc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["vc_id"] = channel.id

    await bot.save_config_to_db(interaction.guild)
    await bot.ensure_vc_connection(interaction.guild)

    await interaction.followup.send(f"🔊 Joined {channel.mention}, saved to DB, and auto-reconnect is active!", ephemeral=True)


@set_group.command(name="db", description="Set the Database channel & restore all configurations")
@app_commands.describe(channel="Select the private DB text channel")
async def set_db(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    guild_id = guild.id

    config = bot.configs.setdefault(guild_id, {})
    config["db_channel_id"] = channel.id

    latest_config = None
    latest_config_msg_id = None

    async for msg in channel.history(limit=None, oldest_first=True):
        if msg.author.id != bot.user.id:
            continue
        raw = msg.content.strip()
        if raw.startswith("```json") and raw.endswith("```"):
            raw = raw[7:-3].strip()
        try:
            data = json.loads(raw)
            if data.get("type") == "STATS_CONFIG":
                latest_config = data
                latest_config_msg_id = msg.id
        except json.JSONDecodeError:
            continue

    if latest_config:
        for k in [
            "vc_id", "all_members_ch", "all_bots_ch",
            "online_members_ch", "online_bots_ch",
            "verified_members_ch", "paid_users_ch",
            "verified_role_id", "paid_role_id"
        ]:
            if latest_config.get(k):
                config[k] = latest_config[k]

        config["config_msg_id"] = latest_config_msg_id

        await bot.ensure_vc_connection(guild)
        await bot.update_guild_stats(guild)

        await interaction.followup.send(
            f"✅ **Stats Database Synced & Restored from {channel.mention}!**\n"
            f"• **Stats Channels:** Updated\n"
            f"• **Voice Channel:** Connected automatically",
            ephemeral=True
        )
    else:
        await bot.save_config_to_db(guild)
        await interaction.followup.send(
            f"✅ **Stats Database Initialized in {channel.mention}!**\n"
            f"Now set your stats channels & roles using `/set all members`, `/set online members`, etc.",
            ephemeral=True
        )


bot.tree.add_command(set_group)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("STATS_TOKEN or DISCORD_TOKEN environment variable not found!")
    bot.run(TOKEN)
