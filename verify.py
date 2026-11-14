import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Start Verification",
        style=discord.ButtonStyle.success,
        emoji="🛡️",
        custom_id="clouskee_verify_btn"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot: ClouskeeBot = interaction.client
        guild_id = interaction.guild.id
        config = bot.configs.get(guild_id, {})

        role_id = config.get("role_id")
        db_channel_id = config.get("db_channel_id")

        if not role_id or not db_channel_id:
            return await interaction.response.send_message(
                "⚠️ Verification system is not fully configured yet. Please contact the Server Owner.",
                ephemeral=True
            )

        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message(
                "⚠️ Verified role not found! Please contact an admin.",
                ephemeral=True
            )

        if role in interaction.user.roles:
            return await interaction.response.send_message(
                "✅ **You are already verified in Clouskee!**",
                ephemeral=True
            )

        try:
            await interaction.user.add_roles(role, reason="Clouskee Verification System")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Bot doesn't have permission to assign the role. Move the bot's role above the verified role!",
                ephemeral=True
            )

        if interaction.user.id not in bot.verified_users.get(guild_id, set()):
            db_channel = interaction.guild.get_channel(db_channel_id)
            if db_channel:
                user_record = {
                    "type": "VERIFIED_USER",
                    "user_id": interaction.user.id,
                    "username": str(interaction.user)
                }
                await db_channel.send(f"```json\n{json.dumps(user_record)}\n```")
                bot.verified_users.setdefault(guild_id, set()).add(interaction.user.id)

        after_embed = discord.Embed(
            title="🎉 Verification Successful!",
            description=(
                f"Welcome to **Clouskee**, {interaction.user.mention}!\n\n"
                f"🔓 **Unlocked:** Full community access, premium cheats & tools channels, and support tickets.\n"
                f"📌 **Assigned Role:** {role.mention}\n\n"
                f"*Enjoy your stay and follow the server rules!*"
            ),
            color=0x00FF88
        )
        after_embed.set_footer(text="Developed By Clouskee • Security System")
        await interaction.response.send_message(embed=after_embed, ephemeral=True)


def is_server_owner(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id


set_group = app_commands.Group(name="set", description="Clouskee Verification & System Configuration (Owner Only)")
verify_sub = app_commands.Group(name="verify", description="Configure verification settings", parent=set_group)


@verify_sub.command(name="role", description="Set the role given to users after verification")
@app_commands.describe(role="Select the verified member role")
async def set_verify_role(interaction: discord.Interaction, role: discord.Role):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Only the Server Owner can use this command.", ephemeral=True)

    bot: ClouskeeBot = interaction.client
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["role_id"] = role.id
    await bot.save_config_to_db(interaction.guild)

    await interaction.response.send_message(
        f"✅ Verified role set to {role.mention} and saved to DB!",
        ephemeral=True
    )


@verify_sub.command(name="channel", description="Set the channel where the verification panel will be posted")
@app_commands.describe(channel="Select the verification text channel")
async def set_verify_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Only the Server Owner can use this command.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    bot: ClouskeeBot = interaction.client
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["verify_channel_id"] = channel.id

    await bot.refresh_verify_message(interaction.guild)
    await interaction.followup.send(
        f"✅ Verification embed posted in {channel.mention} and saved to DB!",
        ephemeral=True
    )


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the bot")
@app_commands.describe(channel="Select the voice channel")
async def set_vc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Only the Server Owner can use this command.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    bot: ClouskeeBot = interaction.client
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["vc_id"] = channel.id

    await bot.save_config_to_db(interaction.guild)
    await bot.ensure_vc_connection(interaction.guild)

    await interaction.followup.send(
        f"🔊 Joined {channel.mention}, saved to DB, and auto-reconnect is active!",
        ephemeral=True
    )


@set_group.command(name="db", description="Set the Database channel & restore all saved data/messages")
@app_commands.describe(channel="Select the private DB text channel")
async def set_db(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Only the Server Owner can use this command.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    bot: ClouskeeBot = interaction.client
    guild = interaction.guild
    guild_id = guild.id

    config = bot.configs.setdefault(guild_id, {})
    config["db_channel_id"] = channel.id
    bot.verified_users[guild_id] = set()

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
            if data.get("type") == "CONFIG":
                latest_config = data
                latest_config_msg_id = msg.id
            elif data.get("type") == "VERIFIED_USER":
                uid = data.get("user_id")
                if uid:
                    bot.verified_users[guild_id].add(int(uid))
        except json.JSONDecodeError:
            continue

    if latest_config:
        if latest_config.get("role_id"):
            config["role_id"] = latest_config["role_id"]
        if latest_config.get("vc_id"):
            config["vc_id"] = latest_config["vc_id"]
        if latest_config.get("verify_channel_id"):
            config["verify_channel_id"] = latest_config["verify_channel_id"]
        if latest_config.get("verify_msg_id"):
            config["verify_msg_id"] = latest_config["verify_msg_id"]
        config["config_msg_id"] = latest_config_msg_id

        await bot.refresh_verify_message(guild)
        await bot.ensure_vc_connection(guild)

        await interaction.followup.send(
            f"✅ **Database Synced & Restored from {channel.mention}!**\n"
            f"• **Verified Users Loaded:** `{len(bot.verified_users[guild_id])}`\n"
            f"• **Verify Embed:** Refreshed (Old deleted, new posted)\n"
            f"• **Voice Channel:** Connected automatically",
            ephemeral=True
        )
    else:
        await bot.save_config_to_db(guild)
        await interaction.followup.send(
            f"✅ **Database Initialized in {channel.mention}!**\n"
            f"Now set your role, channel, and VC using `/set verify role`, `/set verify channel`, and `/set vc`.",
            ephemeral=True
        )


class ClouskeeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}
        self.verified_users = {}

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.tree.add_command(set_group)
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Security 🛡️")
        )

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id == self.user.id:
            guild = member.guild
            config = self.configs.get(guild.id, {})
            target_vc_id = config.get("vc_id")

            if target_vc_id and (after.channel is None or after.channel.id != target_vc_id):
                await asyncio.sleep(2)
                await self.ensure_vc_connection(guild)

    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        guild_id = guild.id
        if member.id in self.verified_users.get(guild_id, set()):
            role_id = self.configs.get(guild_id, {}).get("role_id")
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    try:
                        await member.add_roles(role, reason="Clouskee DB Auto-Restore on Rejoin")
                    except discord.Forbidden:
                        pass

    def build_verify_embed(self, guild: discord.Guild) -> discord.Embed:
        embed = discord.Embed(
            title="🛡️ Welcome to Clouskee",
            description=(
                "Welcome to the official **Clouskee** Discord Server! Your premier destination for "
                "exclusive **Game Cheats**, **Custom Tools**, **Scripts**, and a thriving gaming community.\n\n"
                "To unlock full access to our cheats, channels, and open **support tickets**, "
                "please click the **Start Verification** button below to verify your account."
            ),
            color=0xFF6B00
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(
            name="⚡ Instant Access",
            value="Click the green button below to get your member role immediately.",
            inline=False
        )
        embed.set_footer(text="Developed By Clouskee")
        return embed

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
            "type": "CONFIG",
            "role_id": config.get("role_id"),
            "vc_id": config.get("vc_id"),
            "verify_channel_id": config.get("verify_channel_id"),
            "verify_msg_id": config.get("verify_msg_id")
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
            print(f"❌ [VC Error] Could not join VC in {guild.name}: {e}")

    async def refresh_verify_message(self, guild: discord.Guild):
        config = self.configs.get(guild.id, {})
        verify_ch_id = config.get("verify_channel_id")
        if not verify_ch_id:
            return

        verify_channel = guild.get_channel(verify_ch_id)
        if not verify_channel:
            return

        old_msg_id = config.get("verify_msg_id")
        if old_msg_id:
            try:
                old_msg = await verify_channel.fetch_message(old_msg_id)
                await old_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        embed = self.build_verify_embed(guild)
        new_msg = await verify_channel.send(embed=embed, view=VerifyView())
        config["verify_msg_id"] = new_msg.id
        await self.save_config_to_db(guild)
