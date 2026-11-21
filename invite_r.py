import os
import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("INVITE_R_DISCORD_BOT")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.invites = True
intents.voice_states = True
intents.message_content = True


class RejectReasonModal(discord.ui.Modal, title="Reject Custom Role Request"):
    reason_input = discord.ui.TextInput(
        label="Rejection Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Enter reason for rejecting this custom role...",
        required=True,
        max_length=500
    )

    def __init__(self, bot_instance, guild_id: int, requester_id: int, role_name: str, cost: int, request_msg: discord.Message):
        super().__init__()
        self.bot = bot_instance
        self.guild_id = guild_id
        self.requester_id = requester_id
        self.role_name = role_name
        self.cost = cost
        self.request_msg = request_msg

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value.strip()
        guild = self.bot.get_guild(self.guild_id)

        # Refund invites/coins
        self.bot.add_user_invites(self.guild_id, self.requester_id, self.cost)
        await self.bot.save_data_to_db(guild) if guild else None

        if guild:
            member = guild.get_member(self.requester_id)
            if member:
                try:
                    dm_embed = discord.Embed(
                        title="❌ Custom Role Request Rejected",
                        description=(
                            f"Your custom role request (**{self.role_name}**) in **{guild.name}** was **rejected**.\n\n"
                            f"📝 **Reason:** {reason}\n"
                            f"♻️ **Refunded:** `{self.cost}` invites have been returned to your balance."
                        ),
                        color=0xFF3333
                    )
                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    pass

        updated_embed = self.request_msg.embeds[0]
        updated_embed.color = 0xFF3333
        updated_embed.add_field(name="Status", value=f"❌ Rejected by {interaction.user.mention}\n**Reason:** {reason}", inline=False)
        await self.request_msg.edit(embed=updated_embed, view=None)

        await interaction.response.send_message(
            f"✅ Rejected `{self.role_name}` and refunded `{self.cost}` invites to <@{self.requester_id}>.",
            ephemeral=True
        )


class CustomRoleApprovalView(discord.ui.View):
    def __init__(self, bot_instance, guild_id: int, requester_id: int, role_name: str, role_color_hex: str, cost: int):
        super().__init__(timeout=None)
        self.bot = bot_instance
        self.guild_id = guild_id
        self.requester_id = requester_id
        self.role_name = role_name
        self.role_color_hex = role_color_hex
        self.cost = cost

    @discord.ui.button(label="Accept Role", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            return await interaction.response.send_message("❌ Server not found.", ephemeral=True)

        member = guild.get_member(self.requester_id)
        if not member:
            return await interaction.response.send_message("❌ Member is no longer in the server.", ephemeral=True)

        try:
            hex_clean = self.role_color_hex.lstrip("#")
            color_val = discord.Color(int(hex_clean, 16))
        except Exception:
            color_val = discord.Color.blurple()

        try:
            created_role = await guild.create_role(
                name=self.role_name,
                color=color_val,
                reason=f"Approved custom reward role for {member}"
            )
            await member.add_roles(created_role, reason="Custom reward role approved")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Bot lacks permission to create or assign roles! Check bot role hierarchy & permissions.",
                ephemeral=True
            )

        try:
            dm_embed = discord.Embed(
                title="🎉 Custom Role Approved!",
                description=(
                    f"Your custom role request in **{guild.name}** has been **approved**!\n\n"
                    f"🏷️ **Role:** {created_role.mention} (`{self.role_name}`)\n"
                    f"🎨 **Color:** `{self.role_color_hex}`"
                ),
                color=0x00FF88
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        embed = interaction.message.embeds[0]
        embed.color = 0x00FF88
        embed.add_field(name="Status", value=f"✅ Accepted by {interaction.user.mention} (Role: {created_role.mention})", inline=False)
        await interaction.message.edit(embed=embed, view=None)

        await interaction.response.send_message(f"✅ Created and assigned {created_role.mention} to {member.mention}!", ephemeral=True)

    @discord.ui.button(label="Reject & Refund", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RejectReasonModal(
            bot_instance=self.bot,
            guild_id=self.guild_id,
            requester_id=self.requester_id,
            role_name=self.role_name,
            cost=self.cost,
            request_msg=interaction.message
        )
        await interaction.response.send_modal(modal)


class CustomRoleRequestModal(discord.ui.Modal, title="Request Custom Name Role (20 Invites)"):
    role_name_input = discord.ui.TextInput(
        label="Custom Role Name",
        placeholder="e.g. Dark Legend",
        required=True,
        max_length=60
    )
    role_color_input = discord.ui.TextInput(
        label="Role Color (Hex Code)",
        placeholder="e.g. #FFB703 or #00FF88",
        required=True,
        max_length=10
    )

    def __init__(self, bot_instance, guild: discord.Guild, cost: int = 20):
        super().__init__()
        self.bot = bot_instance
        self.guild = guild
        self.cost = cost

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = self.guild.id
        user_id = interaction.user.id
        current_bal = self.bot.get_user_invites(guild_id, user_id)

        if current_bal < self.cost:
            return await interaction.response.send_message(
                f"❌ You need **{self.cost}** invites, but you only have **`{current_bal}`**.",
                ephemeral=True
            )

        self.bot.add_user_invites(guild_id, user_id, -self.cost)
        await self.bot.save_data_to_db(self.guild)

        role_name = self.role_name_input.value.strip()
        color_hex = self.role_color_input.value.strip()
        if not color_hex.startswith("#"):
            color_hex = f"#{color_hex}"

        owner = self.guild.owner
        sent_to_owner = False
        if owner:
            owner_embed = discord.Embed(
                title="👑 Custom Name Role Request (20 Invites)",
                description=(
                    f"**Server:** {self.guild.name}\n"
                    f"**Requested by:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Role Name:** `{role_name}`\n"
                    f"**Role Color:** `{color_hex}`\n"
                    f"**Deducted Invites:** `{self.cost}`"
                ),
                color=0xFFB703
            )
            view = CustomRoleApprovalView(self.bot, guild_id, user_id, role_name, color_hex, self.cost)
            try:
                await owner.send(embed=owner_embed, view=view)
                sent_to_owner = True
            except discord.Forbidden:
                sent_to_owner = False

        if not sent_to_owner:
            # Refund automatically if owner DM cannot be reached
            self.bot.add_user_invites(guild_id, user_id, self.cost)
            await self.bot.save_data_to_db(self.guild)
            return await interaction.response.send_message(
                "⚠️ Could not DM the Server Owner. Your invites have been refunded automatically.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"📩 Your request for role **`{role_name}`** (`{color_hex}`) has been sent to the Server Owner for approval!",
            ephemeral=True
        )


class ClouskeeInviteBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}
        # {guild_id: {code: uses}}
        self.invite_cache = {}
        # {guild_id: {str(user_id): int_invites}}
        self.user_invites = {}
        # {guild_id: {"vpn_7d": [...], "vpn_30d": [...], "quest_code": str | None}}
        self.rewards_pool = {}

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Invite & Rewards Bot Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Invites & Rewards 🎁")
        )
        for guild in self.guilds:
            await self.cache_guild_invites(guild)
            await self.ensure_vc_connection(guild)

    async def cache_guild_invites(self, guild: discord.Guild):
        try:
            invites = await guild.invites()
            self.invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
        except discord.Forbidden:
            self.invite_cache[guild.id] = {}

    def get_guild_pool(self, guild_id: int) -> dict:
        return self.rewards_pool.setdefault(guild_id, {
            "vpn_7d": [],
            "vpn_30d": [],
            "quest_code": None
        })

    def get_user_invites(self, guild_id: int, user_id: int) -> int:
        return self.user_invites.setdefault(guild_id, {}).get(str(user_id), 0)

    def add_user_invites(self, guild_id: int, user_id: int, delta: int) -> int:
        guild_map = self.user_invites.setdefault(guild_id, {})
        current = guild_map.get(str(user_id), 0)
        new_val = max(0, current + delta)
        guild_map[str(user_id)] = new_val
        return new_val

    async def save_data_to_db(self, guild: discord.Guild):
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
            "type": "INVITE_REWARDS_DB",
            "vc_id": config.get("vc_id"),
            "notice_channel_id": config.get("notice_channel_id"),
            "user_invites": self.user_invites.get(guild_id, {}),
            "rewards_pool": self.get_guild_pool(guild_id)
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
            print(f"[VC Error] Invite Bot could not join VC: {e}")


bot = ClouskeeInviteBot()


@bot.event
async def on_invite_create(invite: discord.Invite):
    guild_cache = bot.invite_cache.setdefault(invite.guild.id, {})
    guild_cache[invite.code] = invite.uses


@bot.event
async def on_invite_delete(invite: discord.Invite):
    guild_cache = bot.invite_cache.setdefault(invite.guild.id, {})
    guild_cache.pop(invite.code, None)


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
async def on_member_join(member: discord.Member):
    if member.bot:
        return

    guild = member.guild
    old_uses = bot.invite_cache.get(guild.id, {})
    inviter = None
    used_code = None

    try:
        current_invites = await guild.invites()
    except discord.Forbidden:
        return

    new_cache = {}
    for inv in current_invites:
        new_cache[inv.code] = inv.uses
        prev_count = old_uses.get(inv.code, 0)
        if inv.uses > prev_count and inviter is None:
            inviter = inv.inviter
            used_code = inv.code

    bot.invite_cache[guild.id] = new_cache

    if inviter and not inviter.bot:
        new_total = bot.add_user_invites(guild.id, inviter.id, 1)
        await bot.save_data_to_db(guild)

        config = bot.configs.get(guild.id, {})
        notice_ch_id = config.get("notice_channel_id")
        if notice_ch_id:
            notice_ch = guild.get_channel(notice_ch_id)
            if notice_ch:
                embed = discord.Embed(
                    title="📨 New Member Joined via Invite",
                    description=(
                        f"👋 **Joined Member:** {member.mention}\n"
                        f"🎟️ **Invited By:** {inviter.mention}\n"
                        f"🔑 **Invite Code:** `{used_code}`\n"
                        f"🪙 **Inviter Balance:** `{new_total}` invites/coins"
                    ),
                    color=0x00FF88
                )
                embed.set_footer(text="Clouskee Invite Tracker")
                await notice_ch.send(content=f"{member.mention} {inviter.mention}", embed=embed)


# ==================== SLASH COMMANDS ====================

def is_server_owner(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id


set_group = app_commands.Group(name="set", description="Clouskee Invite & Rewards Setup (Owner Only)")


@set_group.command(name="notice", description="Set the Notice Channel for invite join alerts")
@app_commands.describe(channel="Select the text channel")
async def set_notice_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    bot.configs.setdefault(interaction.guild.id, {})["notice_channel_id"] = channel.id
    await bot.save_data_to_db(interaction.guild)
    await interaction.response.send_message(f"✅ Notice channel set to {channel.mention} and saved to DB!", ephemeral=True)


@set_group.command(name="vpn7", description="Add 7 Days Zoom Package VPN codes/configs (comma or newline separated)")
@app_commands.describe(items="Enter VPN codes/configs to add to stock")
async def set_vpn7(interaction: discord.Interaction, items: str):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    new_items = [x.strip() for x in items.replace("\n", ",").split(",") if x.strip()]
    pool = bot.get_guild_pool(interaction.guild.id)
    pool["vpn_7d"].extend(new_items)
    await bot.save_data_to_db(interaction.guild)

    await interaction.response.send_message(
        f"✅ Added **`{len(new_items)}`** items to **7 Days Zoom VPN** stock.\n"
        f"📦 Current Stock: **`{len(pool['vpn_7d'])}`**",
        ephemeral=True
    )


@set_group.command(name="vpn30", description="Add 1 Month Package VPN codes/configs (comma or newline separated)")
@app_commands.describe(items="Enter VPN codes/configs to add to stock")
async def set_vpn30(interaction: discord.Interaction, items: str):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    new_items = [x.strip() for x in items.replace("\n", ",").split(",") if x.strip()]
    pool = bot.get_guild_pool(interaction.guild.id)
    pool["vpn_30d"].extend(new_items)
    await bot.save_data_to_db(interaction.guild)

    await interaction.response.send_message(
        f"✅ Added **`{len(new_items)}`** items to **1 Month VPN** stock.\n"
        f"📦 Current Stock: **`{len(pool['vpn_30d'])}`**",
        ephemeral=True
    )


@set_group.command(name="questcode", description="Set the Discord Console Quest Completer code (unlimited)")
@app_commands.describe(code="Enter the quest completer code/instructions")
async def set_quest_code(interaction: discord.Interaction, code: str):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    pool = bot.get_guild_pool(interaction.guild.id)
    pool["quest_code"] = code.strip()
    await bot.save_data_to_db(interaction.guild)

    await interaction.response.send_message("✅ **Discord Console Quest Completer** code updated (Unlimited stock).", ephemeral=True)


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the Invite Bot")
@app_commands.describe(channel="Select the voice channel")
async def set_vc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    bot.configs.setdefault(interaction.guild.id, {})["vc_id"] = channel.id
    await bot.save_data_to_db(interaction.guild)
    await bot.ensure_vc_connection(interaction.guild)
    await interaction.followup.send(f"🔊 Joined {channel.mention}, saved to DB, and auto-reconnect is active!", ephemeral=True)


@set_group.command(name="db", description="Set the Database channel & restore invites, stocks, and configs")
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
            if parsed.get("type") == "INVITE_REWARDS_DB":
                latest_data = parsed
                latest_msg_id = msg.id
        except json.JSONDecodeError:
            continue

    if latest_data:
        if latest_data.get("vc_id"):
            config["vc_id"] = latest_data["vc_id"]
        if latest_data.get("notice_channel_id"):
            config["notice_channel_id"] = latest_data["notice_channel_id"]
        bot.user_invites[guild_id] = latest_data.get("user_invites", {})
        pool = latest_data.get("rewards_pool", {})
        bot.rewards_pool[guild_id] = {
            "vpn_7d": pool.get("vpn_7d", []),
            "vpn_30d": pool.get("vpn_30d", []),
            "quest_code": pool.get("quest_code")
        }
        config["db_msg_id"] = latest_msg_id
        await bot.ensure_vc_connection(guild)
        await bot.cache_guild_invites(guild)

        await interaction.followup.send(
            f"✅ **Invite & Rewards Database Restored from {channel.mention}!**\n"
            f"• **Tracked Users:** `{len(bot.user_invites[guild_id])}`\n"
            f"• **7D Zoom VPN Stock:** `{len(bot.rewards_pool[guild_id]['vpn_7d'])}`\n"
            f"• **1M VPN Stock:** `{len(bot.rewards_pool[guild_id]['vpn_30d'])}`",
            ephemeral=True
        )
    else:
        await bot.save_data_to_db(guild)
        await interaction.followup.send(
            f"✅ **Invite & Rewards Database Initialized in {channel.mention}!**",
            ephemeral=True
        )


@bot.tree.command(name="invites", description="Check your or another member's invite/coin balance")
@app_commands.describe(member="Select a member (optional)")
async def invites_cmd(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    bal = bot.get_user_invites(interaction.guild.id, target.id)
    await interaction.response.send_message(f"🎟️ {target.mention} has **`{bal}`** invites/coins.", ephemeral=True)


@bot.tree.command(name="transfer", description="Send your invites/coins to another member")
@app_commands.describe(member="Member to receive invites", amount="Number of invites to send")
async def transfer_cmd(interaction: discord.Interaction, member: discord.Member, amount: int):
    if member.bot or member.id == interaction.user.id:
        return await interaction.response.send_message("❌ Invalid recipient.", ephemeral=True)
    if amount <= 0:
        return await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)

    guild_id = interaction.guild.id
    sender_bal = bot.get_user_invites(guild_id, interaction.user.id)
    if sender_bal < amount:
        return await interaction.response.send_message(
            f"❌ Insufficient balance! You only have **`{sender_bal}`** invites.",
            ephemeral=True
        )

    bot.add_user_invites(guild_id, interaction.user.id, -amount)
    new_recv_bal = bot.add_user_invites(guild_id, member.id, amount)
    await bot.save_data_to_db(interaction.guild)

    await interaction.response.send_message(
        f"✅ Transferred **`{amount}`** invites to {member.mention}! (Their balance: `{new_recv_bal}`)"
    )


@bot.tree.command(name="leaderboard", description="Show the top inviters leaderboard")
async def leaderboard_cmd(interaction: discord.Interaction):
    guild_map = bot.user_invites.get(interaction.guild.id, {})
    sorted_users = sorted(guild_map.items(), key=lambda x: x[1], reverse=True)[:10]

    if not sorted_users:
        return await interaction.response.send_message("📊 No invite records found yet.", ephemeral=True)

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for idx, (uid_str, count) in enumerate(sorted_users):
        prefix = medals[idx] if idx < 3 else f"**#{idx + 1}**"
        lines.append(f"{prefix} <@{uid_str}> — **`{count}`** invites")

    embed = discord.Embed(
        title=f"🏆 {interaction.guild.name} Invite Leaderboard",
        description="\n".join(lines),
        color=0xFFB703
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="store", description="View the Clouskee Rewards Mini Store & live stock")
async def store_cmd(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    bal = bot.get_user_invites(guild_id, interaction.user.id)
    pool = bot.get_guild_pool(guild_id)

    vpn7_stock = len(pool["vpn_7d"])
    vpn30_stock = len(pool["vpn_30d"])
    quest_available = "✅ Available" if pool.get("quest_code") else "❌ Not Set"

    vpn7_status = f"Stock: `{vpn7_stock}`" if vpn7_stock > 0 else "❌ **Out of Stock**"
    vpn30_status = f"Stock: `{vpn30_stock}`" if vpn30_stock > 0 else "❌ **Out of Stock**"

    embed = discord.Embed(
        title="🛒 Clouskee Mini Rewards Store",
        description=(
            f"🎟️ **Your Balance:** `{bal}` invites\n"
            f"Use `/redeem` to claim an item!\n\n"
            f"**1. 7 Days Zoom Package VPN** — `3` invites ({vpn7_status})\n"
            f"**2. 1 Month Package VPN** — `10` invites ({vpn30_status})\n"
            f"**3. Discord Console Quest Completer** — `7` invites (`Unlimited` | {quest_available})\n"
            f"**4. Custom Name Role** — `20` invites (`Owner Approval`)"
        ),
        color=0x00B4D8
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="redeem", description="Redeem a reward from the Mini Store")
@app_commands.describe(item="Choose the reward you want to redeem")
@app_commands.choices(item=[
    app_commands.Choice(name="7 Days Zoom Package VPN (3 Invites)", value="vpn7"),
    app_commands.Choice(name="1 Month Package VPN (10 Invites)", value="vpn30"),
    app_commands.Choice(name="Discord Console Quest Completer (7 Invites)", value="quest"),
    app_commands.Choice(name="Custom Name Role - Owner Check (20 Invites)", value="role")
])
async def redeem_cmd(interaction: discord.Interaction, item: str):
    guild = interaction.guild
    guild_id = guild.id
    user_id = interaction.user.id
    bal = bot.get_user_invites(guild_id, user_id)
    pool = bot.get_guild_pool(guild_id)

    if item == "role":
        if bal < 20:
            return await interaction.response.send_message(
                f"❌ You need **`20`** invites for a Custom Name Role. Current balance: `{bal}`.",
                ephemeral=True
            )
        return await interaction.response.send_modal(CustomRoleRequestModal(bot, guild, cost=20))

    costs = {"vpn7": 3, "vpn30": 10, "quest": 7}
    cost = costs[item]

    if bal < cost:
        return await interaction.response.send_message(
            f"❌ You need **`{cost}`** invites, but you have **`{bal}`**.",
            ephemeral=True
        )

    if item == "vpn7":
        if not pool["vpn_7d"]:
            return await interaction.response.send_message("❌ **7 Days Zoom Package VPN** is currently out of stock!", ephemeral=True)
        reward_code = pool["vpn_7d"].pop(0)
        reward_title = "7 Days Zoom Package VPN"

    elif item == "vpn30":
        if not pool["vpn_30d"]:
            return await interaction.response.send_message("❌ **1 Month Package VPN** is currently out of stock!", ephemeral=True)
        reward_code = pool["vpn_30d"].pop(0)
        reward_title = "1 Month Package VPN"

    else:  # quest (unlimited)
        if not pool.get("quest_code"):
            return await interaction.response.send_message("❌ Discord Console Quest Completer code is not set yet!", ephemeral=True)
        reward_code = pool["quest_code"]
        reward_title = "Discord Console Quest Completer"

    bot.add_user_invites(guild_id, user_id, -cost)
    await bot.save_data_to_db(guild)

    dm_embed = discord.Embed(
        title=f"🎁 Reward Redeemed: {reward_title}",
        description=(
            f"Thank you for inviting members to **{guild.name}**!\n\n"
            f"🔑 **Your Code / Details:**\n`{reward_code}`\n\n"
            f"🎟️ **Remaining Balance:** `{bot.get_user_invites(guild_id, user_id)}`"
        ),
        color=0x00FF88
    )

    try:
        await interaction.user.send(embed=dm_embed)
        await interaction.response.send_message(
            f"✅ Redeemed **{reward_title}** (`{cost}` invites)! Check your DMs for the reward.",
            ephemeral=True
        )
    except discord.Forbidden:
        # Refund if DM is closed so the code isn't lost
        bot.add_user_invites(guild_id, user_id, cost)
        if item == "vpn7":
            pool["vpn_7d"].insert(0, reward_code)
        elif item == "vpn30":
            pool["vpn_30d"].insert(0, reward_code)
        await bot.save_data_to_db(guild)
        await interaction.response.send_message(
            "⚠️ Please open your DMs so I can send your reward! Your invites and stock were refunded.",
            ephemeral=True
        )


bot.tree.add_command(set_group)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("INVITE_DISCORD_TOKEN (or INVITE_TOKEN / DISCORD_TOKEN) environment variable not found!")
    bot.run(TOKEN)
