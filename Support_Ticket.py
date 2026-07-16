import os
import discord
import psycopg2
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("ST_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Database Connection Helper
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Database Table Initialization (Using unique table name 'ticket_bot_config')
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Unique Configuration Table for this Bot
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_bot_config (
            guild_id BIGINT PRIMARY KEY,
            vc_id BIGINT,
            sc_id BIGINT,
            category_id BIGINT,
            support_role_id BIGINT
        );
    """)
    # Tickets Tracking Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            channel_id BIGINT PRIMARY KEY,
            creator_id BIGINT,
            ticket_type VARCHAR(50)
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Database Functions
def update_config(guild_id, key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO ticket_bot_config (guild_id, {key}) 
        VALUES (%s, %s)
        ON CONFLICT (guild_id) 
        DO UPDATE SET {key} = EXCLUDED.{key};
    """, (guild_id, value))
    conn.commit()
    cursor.close()
    conn.close()

def get_config(guild_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vc_id, sc_id, category_id, support_role_id FROM ticket_bot_config WHERE guild_id = %s;", (guild_id,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    if res:
        return {"vc_id": res[0], "sc_id": res[1], "category_id": res[2], "support_role_id": res[3]}
    return None

def save_ticket(channel_id, creator_id, ticket_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (channel_id, creator_id, ticket_type) VALUES (%s, %s, %s);", (channel_id, creator_id, ticket_type))
    conn.commit()
    cursor.close()
    conn.close()

def get_ticket(channel_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT creator_id, ticket_type FROM tickets WHERE channel_id = %s;", (channel_id,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    if res:
        return {"creator_id": res[0], "ticket_type": res[1]}
    return None

# Bot Events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    init_db()  # This will create the new 'ticket_bot_config' table automatically
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    # Auto-join configured Voice Channel
    for guild in bot.guilds:
        config = get_config(guild.id)
        if config and config["vc_id"]:
            vc_channel = guild.get_channel(config["vc_id"])
            if vc_channel and isinstance(vc_channel, discord.VoiceChannel):
                try:
                    await vc_channel.connect()
                    print(f"Joined VC: {vc_channel.name} in {guild.name}")
                except Exception as e:
                    print(f"Failed to join VC in {guild.name}: {e}")

# Admin Slash Commands
@bot.tree.command(name="set_vc", description="Set the voice channel for the bot to join on startup.")
@app_commands.checks.has_permissions(administrator=True)
async def set_vc(interaction: discord.Interaction, channel: discord.VoiceChannel):
    update_config(interaction.guild_id, "vc_id", channel.id)
    await interaction.response.send_message(f"Voice channel set to {channel.mention}", ephemeral=True)

@bot.tree.command(name="set_sc", description="Set the Support Ticket Create Channel.")
@app_commands.checks.has_permissions(administrator=True)
async def set_sc(interaction: discord.Interaction, channel: discord.TextChannel):
    update_config(interaction.guild_id, "sc_id", channel.id)
    
    # Send Ticket Panel with Select Menu
    embed = discord.Embed(
        title="📩 Support Ticket Panel",
        description="To start a support ticket, please choose the relevant category from the drop-down menu below.",
        color=discord.Color.blue()
    )
    view = TicketDropdownView()
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"Support Channel set to {channel.mention} and panel sent!", ephemeral=True)

@bot.tree.command(name="set_category", description="Set the category where new tickets will be created.")
@app_commands.checks.has_permissions(administrator=True)
async def set_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    update_config(interaction.guild_id, "category_id", category.id)
    await interaction.response.send_message(f"Ticket Category set to **{category.name}**", ephemeral=True)

@bot.tree.command(name="set_sr", description="Set the Support Role.")
@app_commands.checks.has_permissions(administrator=True)
async def set_sr(interaction: discord.Interaction, role: discord.Role):
    update_config(interaction.guild_id, "support_role_id", role.id)
    await interaction.response.send_message(f"Support Role set to **{role.name}**", ephemeral=True)


# TICKET INTERACTION VIEWS

# Close Button View (Visible inside the ticket channel)
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data = get_ticket(interaction.channel_id)
        config = get_config(interaction.guild_id)
        
        if not ticket_data:
            await interaction.response.send_message("This is not a registered ticket channel.", ephemeral=True)
            return

        creator_id = ticket_data["creator_id"]
        is_creator = interaction.user.id == creator_id
        is_owner = interaction.user.id == interaction.guild.owner_id
        
        support_role_id = config["support_role_id"] if config else None
        
        # Only Creator or Server Owner can close
        if not (is_creator or is_owner):
            await interaction.response.send_message("❌ Only the Ticket Creator or the Server Owner can close this ticket!", ephemeral=True)
            return

        await interaction.response.send_message("Closing ticket and notifying relevant parties...", ephemeral=True)

        # DM Log Message
        embed_dm = discord.Embed(
            title="🎫 Ticket Closed",
            description=f"Ticket channel **#{interaction.channel.name}** has been closed.",
            color=discord.Color.red()
        )
        embed_dm.add_field(name="Closed By", value=interaction.user.mention, inline=True)
        embed_dm.add_field(name="Ticket Type", value=ticket_data["ticket_type"], inline=True)

        # 1. DM Ticket Creator
        try:
            creator = await bot.fetch_user(creator_id)
            await creator.send(embed=embed_dm)
        except Exception:
            pass

        # 2. DM Support Role Users
        if support_role_id:
            support_role = interaction.guild.get_role(support_role_id)
            if support_role:
                for member in support_role.members:
                    if not member.bot:
                        try:
                            await member.send(embed=embed_dm)
                        except Exception:
                            pass

        await interaction.channel.delete(reason="Ticket Closed")


# User Selection View (For Group Tickets)
class GroupMemberSelect(discord.ui.UserSelect):
    def __init__(self, category_name):
        super().__init__(placeholder="Select members to add to your Group Ticket...", min_values=1, max_values=10)
        self.category_name = category_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        config = get_config(guild.id)

        if not config or not config["category_id"] or not config["support_role_id"]:
            await interaction.followup.send("❌ Setup incomplete! Please ask admins to run configuration commands.", ephemeral=True)
            return

        category = guild.get_channel(config["category_id"])
        support_role = guild.get_role(config["support_role_id"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
        }

        selected_members = self.values
        for member in selected_members:
            if isinstance(member, discord.Member):
                overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

        channel_name = f"group-{self.category_name.lower().replace(' ', '-')}-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        save_ticket(ticket_channel.id, interaction.user.id, self.category_name)

        member_mentions = ", ".join([m.mention for m in selected_members])
        embed = discord.Embed(
            title=f"🎫 {self.category_name} Ticket Created",
            description=f"Welcome {interaction.user.mention} and {member_mentions}! Support team will be with you shortly.\nUse the button below to close this ticket.",
            color=discord.Color.green()
        )
        await ticket_channel.send(embed=embed, view=TicketControlView())
        await interaction.followup.send(f"Ticket created successfully: {ticket_channel.mention}", ephemeral=True)


class GroupMemberSelectView(discord.ui.View):
    def __init__(self, category_name):
        super().__init__(timeout=180)
        self.add_item(GroupMemberSelect(category_name))


# Dropdown Menu for choosing Ticket Category
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Report", description="Report a user or behavior.", emoji="🚨"),
            discord.SelectOption(label="Help Us", description="Get regular help from support.", emoji="🙋‍♂️"),
            discord.SelectOption(label="Group Report", description="Create a report with multiple members.", emoji="👥"),
            discord.SelectOption(label="Group Help", description="Group support queries.", emoji="🤝"),
        ]
        super().__init__(placeholder="Choose a ticket category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        guild = interaction.guild
        config = get_config(guild.id)

        if not config or not config["category_id"] or not config["support_role_id"]:
            await interaction.response.send_message("❌ Setup incomplete! Bot category or Support role not configured.", ephemeral=True)
            return

        if selected_value in ["Group Report", "Group Help"]:
            view = GroupMemberSelectView(selected_value)
            await interaction.response.send_message("Please select the members you want to add to this group ticket:", view=view, ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True)
            category = guild.get_channel(config["category_id"])
            support_role = guild.get_role(config["support_role_id"])

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
                support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
            }

            channel_name = f"{selected_value.lower().replace(' ', '-')}-{interaction.user.name}"
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )

            save_ticket(ticket_channel.id, interaction.user.id, selected_value)

            embed = discord.Embed(
                title=f"🎫 {selected_value} Ticket Created",
                description=f"Welcome {interaction.user.mention}! Support team will be with you shortly.\nUse the button below to close this ticket.",
                color=discord.Color.green()
            )
            await ticket_channel.send(embed=embed, view=TicketControlView())
            await interaction.followup.send(f"Ticket created successfully: {ticket_channel.mention}", ephemeral=True)


class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


# Run Bot
bot.run(TOKEN)
