import os
import re
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("SAFER_TOKEN", os.getenv("SAFTER_DISCORD_TOKEN"))

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


class ClouskeeSaferBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}
        self.message_tracker = {}

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Message Safer Bot Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Chat Safety 🛡️")
        )
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
            "type": "SAFER_CONFIG",
            "vc_id": config.get("vc_id"),
            "bad_words": config.get("bad_words", []),
            "approved_links": config.get("approved_links", [])
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
            print(f"[VC Error] Safer Bot could not join VC: {e}")


bot = ClouskeeSaferBot()


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id == bot.user.id:
        guild = member.guild
        config = bot.configs.get(guild.id, {})
        target_vc_id = config.get("vc_id")

        if target_vc_id and (after.channel is None or after.channel.id != target_vc_id):
            await asyncio.sleep(2)
            await bot.ensure_vc_connection(guild)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # Server Owner exemption
    if message.author.id == message.guild.owner_id:
        return await bot.process_commands(message)

    guild_id = message.guild.id
    config = bot.configs.get(guild_id, {})
    content_lower = message.content.lower()

    # 1. BAD WORDS FILTER
    bad_words = config.get("bad_words", [])
    if any(word in content_lower for word in bad_words):
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        warn_embed = discord.Embed(
            title="⚠️ Message Warning",
            description="Your recent message was deleted because it contained prohibited words/phrases.",
            color=0xFF3333
        )
        try:
            await message.author.send(embed=warn_embed)
        except discord.Forbidden:
            pass
        return

    # 2. HACKED ACCOUNT / SCAM POST DETECTION (@everyone + attachments/links)
    is_everyone = "@everyone" in message.content or "@here" in message.content
    has_attachment = len(message.attachments) > 0
    has_link = "http://" in content_lower or "https://" in content_lower

    if is_everyone and (has_attachment or has_link):
        user_id = message.author.id
        import time
        current_time = time.time()
        
        bot.message_tracker.setdefault(user_id, [])
        bot.message_tracker[user_id] = [t for t in bot.message_tracker[user_id] if current_time - t < 60]
        bot.message_tracker[user_id].append(current_time)

        if len(bot.message_tracker[user_id]) >= 2:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            
            hack_warn = discord.Embed(
                title="🛡️ Security Alert: Potential Compromised Account",
                description="Your message was flagged as a potential scam/hack broadcast and was removed automatically.",
                color=0xFF3333
            )
            try:
                await message.author.send(embed=hack_warn)
            except discord.Forbidden:
                pass
            return

    # 3. SPAM & REPEAT MESSAGE PROTECTION
    user_id = message.author.id
    import time
    current_time = time.time()
    bot.message_tracker.setdefault(user_id, [])
    
    recent_msgs = bot.message_tracker.get(f"content_{user_id}", [])
    recent_msgs = [(msg, t) for msg, t in recent_msgs if current_time - t < 10]
    
    exact_matches = [m for m, t in recent_msgs if m == message.content]
    if len(exact_matches) >= 2:
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        try:
            await message.author.send("⚠️ Please do not spam identical messages in the server!")
        except discord.Forbidden:
            pass
        return

    recent_msgs.append((message.content, current_time))
    bot.message_tracker[f"content_{user_id}"] = recent_msgs

    # 4. ANTI-LINK & APPROVED LINKS CHECK
    links = re.findall(r'https?://[^\s]+', message.content)
    if links:
        approved_links = config.get("approved_links", [])
        is_approved = False
        for link in links:
            if any(app_link.lower() in link.lower() for app_link in approved_links):
                is_approved = True
                break
            if "discord.gg/" in link or "discord.com/invite/" in link:
                is_approved = False

        if not is_approved and links:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            try:
                await message.author.send("⚠️ Unapproved links are not allowed in this server!")
            except discord.Forbidden:
                pass
            return

    await bot.process_commands(message)


# ==================== SLASH COMMANDS (OWNER ONLY) ====================

def is_server_owner(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id


set_group = app_commands.Group(name="set", description="Clouskee Safer Bot Configuration (Owner Only)")


@set_group.command(name="badwords", description="Add new bad words to the existing list (separated by commas or spaces)")
@app_commands.describe(words="e.g. word1,word2,word3")
async def set_badwords(interaction: discord.Interaction, words: str):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    
    # Split by comma or space
    new_words = [w.strip().lower() for w in re.split(r'[, ]+', words) if w.strip()]
    
    config = bot.configs.setdefault(guild_id, {})
    existing_words = config.get("bad_words", [])
    
    # Append new words without removing old ones (avoiding duplicates)
    added_count = 0
    for w in new_words:
        if w not in existing_words:
            existing_words.append(w)
            added_count += 1
            
    config["bad_words"] = existing_words
    await bot.save_config_to_db(interaction.guild)

    await interaction.followup.send(
        f"✅ Added `{added_count}` new bad words! Total bad words in filter: **{len(existing_words)}**",
        ephemeral=True
    )


@set_group.command(name="approvel", description="Add an approved safe link domain")
@app_commands.describe(link="e.g. youtube.com or clouskee.vercel.app")
async def set_approval(interaction: discord.Interaction, link: str):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    config = bot.configs.setdefault(guild_id, {})
    
    approved = config.get("approved_links", [])
    link_clean = link.strip()
    if link_clean not in approved:
        approved.append(link_clean)
    config["approved_links"] = approved

    await bot.save_config_to_db(interaction.guild)
    await interaction.followup.send(f"✅ Approved link/domain `{link_clean}` added and saved to DB!", ephemeral=True)


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the Safer Bot")
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


@set_group.command(name="db", description="Set the Database channel & restore all safety configurations")
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
            if data.get("type") == "SAFER_CONFIG":
                latest_config = data
                latest_config_msg_id = msg.id
        except json.JSONDecodeError:
            continue

    if latest_config:
        if latest_config.get("vc_id"):
            config["vc_id"] = latest_config["vc_id"]
        if latest_config.get("bad_words"):
            config["bad_words"] = latest_config["bad_words"]
        if latest_config.get("approved_links"):
            config["approved_links"] = latest_config["approved_links"]
        config["config_msg_id"] = latest_config_msg_id

        await bot.ensure_vc_connection(guild)

        await interaction.followup.send(
            f"✅ **Safer Database Synced & Restored from {channel.mention}!**\n"
            f"• **Bad Words Filter:** Active (`{len(config.get('bad_words', []))}` words loaded)\n"
            f"• **Approved Links:** Loaded (`{len(config.get('approved_links', []))}` links)\n"
            f"• **Voice Channel:** Connected automatically",
            ephemeral=True
        )
    else:
        await bot.save_config_to_db(guild)
        await interaction.followup.send(
            f"✅ **Safer Database Initialized in {channel.mention}!**\n"
            f"Now configure using `/set badwords`, `/set approvel`, and `/set vc`.",
            ephemeral=True
        )


bot.tree.add_command(set_group)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("SAFER_TOKEN or DISCORD_TOKEN environment variable not found!")
    bot.run(TOKEN)
