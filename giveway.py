import os
import json
import random
import asyncio
import datetime
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GIVEWAY_DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


class GiveawayModal(discord.ui.Modal, title="Create Pro Giveaway"):
    title_input = discord.ui.TextInput(
        label="Giveaway Name",
        placeholder="e.g. NITRO BOOST / PREMIUM KEY / V2RAY",
        required=True,
        max_length=100
    )
    details_input = discord.ui.TextInput(
        label="Giveaway Details",
        style=discord.TextStyle.paragraph,
        placeholder="Item : Discord Nitro 1 Month\nFeatures : Custom Emoji & HD Streaming\nValidity : 30 Days\nSource : Official Store",
        required=True,
        max_length=1000
    )
    duration_input = discord.ui.TextInput(
        label="Duration in Hours",
        placeholder="e.g. 24 (for 24 hours)",
        required=True,
        max_length=5
    )
    winners_input = discord.ui.TextInput(
        label="Winners Count",
        placeholder="e.g. 1 or 3",
        required=True,
        max_length=3
    )
    prizes_input = discord.ui.TextInput(
        label="Gift Codes / Prizes (Comma separated)",
        style=discord.TextStyle.paragraph,
        placeholder="Code1-XXXX, Code2-YYYY, Code3-ZZZZ",
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        bot: ClouskeeGiveawayBot = interaction.client
        guild = interaction.guild
        guild_id = guild.id
        config = bot.configs.get(guild_id, {})

        ch_id = config.get("giveaway_channel_id")
        db_channel_id = config.get("db_channel_id")

        if not ch_id or not db_channel_id:
            return await interaction.response.send_message(
                "⚠️ Giveaway channel or Database channel is not configured! Use `/set giveaway channel` and `/set db`.",
                ephemeral=True
            )

        channel = guild.get_channel(ch_id)
        if not channel:
            return await interaction.response.send_message("⚠️ Giveaway channel not found!", ephemeral=True)

        try:
            duration_hours = float(self.duration_input.value.strip())
            winners_count = int(self.winners_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("⚠️ Duration and Winners must be valid numbers!", ephemeral=True)

        prizes = [p.strip() for p in self.prizes_input.value.replace("\n", ",").split(",") if p.strip()]
        if len(prizes) < winners_count:
            return await interaction.response.send_message(
                f"⚠️ You provided only {len(prizes)} gifts, but requested {winners_count} winners! Please provide enough unique gifts.",
                ephemeral=True
            )

        end_time = datetime.datetime.utcnow() + datetime.timedelta(hours=duration_hours)
        end_timestamp = int(end_time.timestamp())

        embed = discord.Embed(
            title=f"🎁 {self.title_input.value.strip()}",
            description=(
                f"{self.details_input.value.strip()}\n\n"
                f"🕒 **Ends At:** <t:{end_timestamp}:F> (<t:{end_timestamp}:R>)\n"
                f"🏆 **Winners:** `{winners_count}`\n"
                f"👤 **Hosted by:** {interaction.user.mention}\n"
                f"📌 **Entries:** `0`"
            ),
            color=0x00FF88
        )
        embed.set_footer(text="Clouskee Giveaway System")

        msg = await channel.send(embed=embed, view=GiveawayJoinView())

        giveaway_data = {
            "message_id": msg.id,
            "channel_id": channel.id,
            "guild_id": guild_id,
            "title": self.title_input.value.strip(),
            "details": self.details_input.value.strip(),
            "host_id": interaction.user.id,
            "winners_count": winners_count,
            "end_time": end_timestamp,
            "prizes": prizes[:winners_count],
            "participants": [],
            "ended": False
        }

        bot.active_giveaways[msg.id] = giveaway_data

        # Save to DB channel
        db_channel = guild.get_channel(db_channel_id)
        if db_channel:
            db_msg = await db_channel.send(f"```json\n{json.dumps(giveaway_data)}\n```")
            giveaway_data["db_msg_id"] = db_msg.id

        await interaction.response.send_message(f"✅ Giveaway successfully created in {channel.mention}!", ephemeral=True)


class GiveawayJoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Join Giveaway",
        style=discord.ButtonStyle.success,
        emoji="🎉",
        custom_id="clouskee_join_giveaway_btn"
    )
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot: ClouskeeGiveawayBot = interaction.client
        msg_id = interaction.message.id
        giveaway = bot.active_giveaways.get(msg_id)

        if not giveaway or giveaway["ended"]:
            return await interaction.response.send_message("❌ This giveaway has already ended or is invalid!", ephemeral=True)

        user_id = interaction.user.id
        if user_id in giveaway["participants"]:
            giveaway["participants"].remove(user_id)
            status_msg = "❌ You have **left** the giveaway."
        else:
            giveaway["participants"].append(user_id)
            status_msg = "✅ You have successfully **joined** the giveaway! Best of luck!"

        # Update embed entry count
        embed = interaction.message.embeds[0]
        desc = embed.description
        lines = desc.split("\n")
        for i, line in enumerate(lines):
            if "Entries:" in line:
                lines[i] = f"📌 **Entries:** `{len(giveaway['participants'])}`"
        embed.description = "\n".join(lines)
        await interaction.message.edit(embed=embed)

        await interaction.response.send_message(status_msg, ephemeral=True)


class ClouskeeGiveawayBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.configs = {}
        self.active_giveaways = {}

    async def setup_hook(self):
        self.add_view(GiveawayJoinView())
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Giveaway Bot Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="Clouskee Giveaways 🎉")
        )
        if not self.giveaway_checker.is_running():
            self.giveaway_checker.start()

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
            "type": "GIVEAWAY_CONFIG",
            "vc_id": config.get("vc_id"),
            "giveaway_channel_id": config.get("giveaway_channel_id")
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
            print(f"[VC Error] Giveaway Bot could not join VC: {e}")

    async def end_giveaway(self, giveaway):
        giveaway["ended"] = True
        guild = self.get_guild(giveaway["guild_id"])
        if not guild:
            return

        channel = guild.get_channel(giveaway["channel_id"])
        if not channel:
            return

        try:
            msg = await channel.fetch_message(giveaway["message_id"])
        except discord.NotFound:
            return

        participants = giveaway["participants"]
        winners_count = giveaway["winners_count"]
        prizes = giveaway["prizes"]

        winners = []
        if participants:
            winners_count = min(winners_count, len(participants))
            winners = random.sample(participants, winners_count)

        winner_mentions = ", ".join([f"<@{uid}>" for uid in winners]) if winners else "No valid entries"

        embed = discord.Embed(
            title=f"🎁 {giveaway['title']} (Ended)",
            description=(
                f"{giveaway['details']}\n\n"
                f"Ended: <t:{giveaway['end_time']}:R> ( <t:{giveaway['end_time']}:F> )\n"
                f"Hosted by: <@{giveaway['host_id']}>\n"
                f"Entries: `{len(participants)}`\n"
                f"Winners: {winner_mentions}"
            ),
            color=0xFFB703
        )
        embed.set_footer(text="Clouskee Giveaway Ended")

        try:
            await msg.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass

        # Send individual prizes to winners via DM
        for idx, winner_id in enumerate(winners):
            winner_member = guild.get_member(winner_id)
            prize_code = prizes[idx] if idx < len(prizes) else "Your special reward!"
            if winner_member:
                dm_embed = discord.Embed(
                    title="🎉 Congratulations! You Won a Giveaway!",
                    description=(
                        f"You won **{giveaway['title']}** in **{guild.name}**!\n\n"
                        f"🎁 **Your Prize / Code:**\n`{prize_code}`\n\n"
                        f"*Enjoy your reward and thank you for participating!*"
                    ),
                    color=0x00FF88
                )
                try:
                    await winner_member.send(embed=dm_embed)
                except discord.Forbidden:
                    pass

    @commands.loop(seconds=10)
    async def giveaway_checker(self):
        current_time = int(datetime.datetime.utcnow().timestamp())
        for msg_id, g in list(self.active_giveaways.items()):
            if not g["ended"] and current_time >= g["end_time"]:
                await self.end_giveaway(g)


bot = ClouskeeGiveawayBot()


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


set_group = app_commands.Group(name="set", description="Clouskee Giveaway Configuration (Owner Only)")
giveaway_sub = app_commands.Group(name="giveaway", description="Configure giveaway settings", parent=set_group)


@giveaway_sub.command(name="channel", description="Set the channel where giveaways will be posted")
@app_commands.describe(channel="Select the text channel")
async def set_giveaway_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    guild_id = interaction.guild.id
    bot.configs.setdefault(guild_id, {})["giveaway_channel_id"] = channel.id
    await bot.save_config_to_db(interaction.guild)

    await interaction.response.send_message(f"✅ Giveaway channel set to {channel.mention} and saved to DB!", ephemeral=True)


@bot.tree.command(name="create", description="Create a new professional giveaway")
async def create_giveaway_slash(interaction: discord.Interaction):
    if not is_server_owner(interaction):
        return await interaction.response.send_message("⛔ **Access Denied:** Server Owner only.", ephemeral=True)

    await interaction.response.send_modal(GiveawayModal())


@set_group.command(name="vc", description="Set the 24/7 Voice Channel for the Giveaway Bot")
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


@set_group.command(name="db", description="Set the Database channel & restore active giveaways")
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
    bot.active_giveaways.clear()

    async for msg in channel.history(limit=None, oldest_first=True):
        if msg.author.id != bot.user.id:
            continue
        raw = msg.content.strip()
        if raw.startswith("```json") and raw.endswith("```"):
            raw = raw[7:-3].strip()
        try:
            data = json.loads(raw)
            if data.get("type") == "GIVEAWAY_CONFIG":
                latest_config = data
            elif "message_id" in data and not data.get("ended"):
                bot.active_giveaways[data["message_id"]] = data
        except json.JSONDecodeError:
            continue

    if latest_config:
        if latest_config.get("vc_id"):
            config["vc_id"] = latest_config["vc_id"]
        if latest_config.get("giveaway_channel_id"):
            config["giveaway_channel_id"] = latest_config["giveaway_channel_id"]

        await bot.ensure_vc_connection(guild)

        await interaction.followup.send(
            f"✅ **Giveaway Database Synced & Restored from {channel.mention}!**\n"
            f"• **Active Giveaways Restored:** `{len(bot.active_giveaways)}`\n"
            f"• **Voice Channel:** Connected automatically",
            ephemeral=True
        )
    else:
        await bot.save_config_to_db(guild)
        await interaction.followup.send(
            f"✅ **Giveaway Database Initialized in {channel.mention}!**\n"
            f"Now set your giveaway channel using `/set giveaway channel` and `/create giveaway`.",
            ephemeral=True
        )


bot.tree.add_command(set_group)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("GIVEAWAY_TOKEN or DISCORD_TOKEN environment variable not found!")
    bot.run(TOKEN)
