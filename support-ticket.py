import os
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("SUPPORT_TOKEN", os.getenv("DISCORD_TOKEN"))

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


class TicketCreateModal(discord.ui.Modal, title="Create Support Ticket"):
    issue = discord.ui.TextInput(
        label="Describe your issue",
        style=discord.TextStyle.paragraph,
        placeholder="Explain your problem or request here...",
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        bot: ClouskeeSupportBot = interaction.client
        guild = interaction.guild
        guild_id = guild.id
        config = bot.configs.get(guild_id, {})

        cate_id = config.get("cate_id")
        role_id = config.get("role_id")
        db_channel_id = config.get("db_channel_id")

        if not cate_id or not role_id or not db_channel_id:
            return await interaction.response.send_message(
                "⚠️ Support system is not fully configured by the server owner yet!",
                ephemeral=True
            )

        category = guild.get_channel(cate_id)
        support_role = guild.get_role(role_id)

        if not category or not support_role:
            return await interaction.response.send_message(
                "⚠️ Support Category or Role not found! Please contact admin.",
                ephemeral=True
            )

        # Increment ticket ID starting from 20
        ticket_id = config.get("ticket_counter", 20)
        config["ticket_counter"] = ticket_id + 1

        channel_name = f"support-ticket-{ticket_id}"

        # Setup permissions (Only User, Bot, and Support Role)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Support ticket opened by {interaction.user}"
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Bot doesn't have permission to create channels in this category!",
                ephemeral=True
            )

        # Save ticket info in memory
        bot.active_tickets[ticket_channel.id] = {
            "ticket_id": ticket_id,
            "user_id": interaction.user.id,
            "claimed_by": None,
            "status": "OPEN"
        }

        # Embed for Ticket Channel & DM
        issue_text = self.issue.value
        embed = discord.Embed(
            title=f"🎫 Support Ticket #{ticket_id}",
            description=(
                f"**Opened by:** {interaction.user.mention}\n\n"
                f"**Issue Description:**\n{issue_text}\n\n"
                f"Support team ({support_role.mention}) will be with you shortly."
            ),
            color=0xFFB703
        )
        embed.set_footer(text="Clouskee Support System")

        # 1. Send message inside the created ticket channel
        await ticket_channel.send(
            content=f"{interaction.user.mention} {support_role.mention}",
            embed=embed,
            view=TicketControlView()
        )

        # 2. Send DM to the ticket opener and all members having the support role
        dm_embed = discord.Embed(
            title=f"🎫 New Support Ticket Opened [#{ticket_id}]",
            description=(
                f"**Server:** {guild.name}\n"
                f"**Opened by:** {interaction.user.mention} (`{interaction.user}`)\n\n"
                f"**Issue:**\n{issue_text}\n\n"
                f"Head over to <#{ticket_channel.id}> to respond."
            ),
            color=0x00B4D8
        )
        dm_embed.set_footer(text="Clouskee Support Notification")

        # DM Ticket Opener
        try:
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        # DM all members having the support role
        for member in support_role.members:
            if member.id != interaction.user.id and not member.bot:
                try:
                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    pass

        # Log ticket creation to DB channel
        db_channel = guild.get_channel(db_channel_id)
        if db_channel:
            record = {
                "type": "TICKET_OPEN",
                "ticket_id": ticket_id,
                "channel_id": ticket_channel.id,
                "user_id": interaction.user.id,
                "status": "OPEN"
            }
            await db_channel.send(f"```json\n{json.dumps(record)}\n```")

        await bot.save_config_to_db(guild)

        await interaction.response.send_message(
            f"✅ Your ticket has been created successfully: {ticket_channel.mention}",
            ephemeral=True
        )


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Support Ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="clouskee_create_ticket_btn"
    )
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal())


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim",
        style=discord.ButtonStyle.success,
        emoji="🙋‍♂️",
        custom_id="clouskee_ticket_claim_btn"
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot: ClouskeeSupportBot = interaction.client
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        ticket_data = bot.active_tickets.get(channel_id)

        if not ticket_data:
            return await interaction.response.send_message("⚠️ Ticket data not found!", ephemeral=True)

        if ticket_data["claimed_by"]:
            return await interaction.response.send_message("⚠️ This ticket is already claimed!", ephemeral=True)

        ticket_data["claimed_by"] = interaction.user.id
        ticket_data["status"] = "CLAIMED"

        await interaction.channel.edit(name=f"claimed-{ticket_data['ticket_id']}")

        embed = discord.Embed(
            title="🙋‍♂️ Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}.",
            color=0x00FF88
        )
        await interaction.channel.send(embed=embed)

        # Log claim to DB
        config = bot.configs.get(guild_id, {})
        db_channel = interaction.guild.get_channel(config.get("db_channel_id"))
        if db_channel:
            record = {
                "type": "TICKET_CLAIM",
                "ticket_id": ticket_data["ticket_id"],
                "claimed_by": interaction.user.id
            }
            await db_channel.send(f"```json\n{json.dumps(record)}\n```")

        await interaction.response.defer()

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="clouskee_ticket_close_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot: ClouskeeSupportBot = interaction.client
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        ticket_data = bot.active_tickets.get(channel_id)

        if not ticket_data:
            return await interaction.response.send_message("⚠️ Ticket data not found!", ephemeral=True)

        ticket_data["status"] = "CLOSED"
        ticket_data["closed_by"] = interaction.user.id

        # Log close to DB including who closed it
        config = bot.configs.get(guild_id, {})
        db_channel = interaction.guild.get_channel(config.get("db_channel_id"))
        if db_channel:
            record = {
                "type": "TICKET_CLOSE",
                "ticket_id": ticket_data["ticket_id"],
                "closed_by": interaction.user.id,
                "user_id": ticket_data["user_id"]
            }
            await db_channel.send(f"```json\n{json.dumps(record)}\n```")

        # Send DM to ticket opener
        close_notice = discord.Embed(
            title="🔒 Support Ticket Closed",
            description=(
                f"Your support ticket **#{ticket_data['ticket_id']}** in **{interaction.guild.name}** "
                f"has been closed by {interaction.user.mention}."
            ),
            color=0xFF3333
        )

        opener = interaction.guild.get_member(ticket_data["user_id"])
        if opener:
            try:
                await opener.send(embed=close_notice)
            except discord.Forbidden:
                pass

        await interaction.response.send_message("🔒 Ticket will be deleted in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except discord.Forbidden:
            pass

        bot.active_tickets.pop(channel_id, None)


class ClouskeeSupportBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}
        self.active_tickets = {}

    async def setup_hook(self):
        self.add_view(TicketPanelView())
        self.add_view(TicketControlView())
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Support Bot Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Tickets 🎫")
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
            "type": "SUPPORT_CONFIG",
            "cate_id": config.get("cate_id"),
            "support_channel_id": config.get("support_channel_id"),
            "role_id": config.get("role_id"),
            "vc_id": config.get("vc_id"),
            "ticket_counter": config.get("ticket_counter", 20),
            "panel_msg_id": config.get("panel_msg_id")
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
            print(f"[VC Error] Support Bot could not join VC: {e}")

    async def refresh_panel(self, guild: discord.Guild):
        config = self.configs.get(guild.id, {})
        ch_id = config.get("support_channel_id")
        if not ch_id:
            return

        channel = guild.get_channel(ch_id)
        if not channel:
            return

        old_id = config.get("panel_msg_id")
        if old_id:
            try:
                old_msg = await channel.fetch_message(old_id)
                await old_msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        embed = discord.Embed(
            title="🎫 Clouskee Support Center",
            description=(
                "Need assistance or have questions regarding our services, VPNs, or cheats?\n\n"
                "Click the **Create Support Ticket** button below to open a private support channel with our team."
            ),
            color=0xFFB703
        )
        embed.set_footer(text="Developed By Clouskee")

        new_msg = await channel.send(embed=embed, view=TicketPanelView())
        config["panel_msg_id"] = new_msg.id
        await self.save_config_to_db(guild)


bot = ClouskeeSupportBot()


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


set_group = app_commands.Group(name="set", description="Clouskee Support Configuration (Owner Only)")
support_sub = app_commands.Group(name="support", description="Configure support ticket settings", parent=set_group)


@support_sub.command(name="cate", description="Set the category where support tickets will be created")
@app_commands.describe(category="Select the category channel")
async def set_support_cate(interaction: discord.Interaction, category: discord.CategoryChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["cate_id"] = category.id
    await bot.save_config_to_db(interaction.guild)

    await interaction.response.send_message(f"✅ Support Category set to **{category.name}** and saved to DB!", ephemeral=True)


@support_sub.command(name="channel", description="Set the channel where the ticket panel will be posted")
@app_commands.describe(channel="Select the text channel")
async def set_support_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["support_channel_id"] = channel.id

    await bot.refresh_panel(interaction.guild)
    await interaction.followup.send(f"✅ Support Panel posted in {channel.mention} and saved to DB!", ephemeral=True)


@support_sub.command(name="role", description="Set the support team role")
@app_commands.describe(role="Select the support role")
async def set_support_role(interaction: discord.Interaction, role: discord.Role):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["role_id"] = role.id
    await bot.save_config_to_db(interaction.guild)

    await interaction.response.send_message(f"✅ Support role set to {role.mention} and saved to DB!", ephemeral=True)


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the Support Bot")
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
            if data.get("type") == "SUPPORT_CONFIG":
                latest_config = data
                latest_config_msg_id = msg.id
        except json.JSONDecodeError:
            continue

    if latest_config:
        config["cate_id"] = latest_config.get("cate_id")
        config["support_channel_id"] = latest_config.get("support_channel_id")
        config["role_id"] = latest_config.get("role_id")
        config["vc_id"] = latest_config.get("vc_id")
        config["ticket_counter"] = latest_config.get("ticket_counter", 20)
        config["panel_msg_id"] = latest_config.get("panel_msg_id")
        config["config_msg_id"] = latest_config_msg_id

        await bot.refresh_panel(guild)
        await bot.ensure_vc_connection(guild)

        await interaction.followup.send(
            f"✅ **Support Database Synced & Restored from {channel.mention}!**\n"
            f"• **Next Ticket ID:** `{config['ticket_counter']}`\n"
            f"• **Panel Message:** Refreshed\n"
            f"• **Voice Channel:** Connected automatically",
            ephemeral=True
        )
    else:
        config["ticket_counter"] = 20
        await bot.save_config_to_db(guild)
        await interaction.followup.send(
            f"✅ **Support Database Initialized in {channel.mention}!**\n"
            f"Now use `/set support cate`, `/set support channel`, `/set support role`, and `/set vc`.",
            ephemeral=True
        )


bot.tree.add_command(set_group)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("SUPPORT_TOKEN or DISCORD_TOKEN environment variable not found!")
    bot.run(TOKEN)
