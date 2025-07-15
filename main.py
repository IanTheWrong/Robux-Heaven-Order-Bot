import discord
from discord.ui import Button, View
from discord.ui import View, Select
import os
from discord.ext import commands

CONFIG_FILE = "config.txt"
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Needed to fetch role members

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Config save/load ---
class MyDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Cryptocurrency", description="Pay with Cryptocurrency", emoji="🔴"),
            discord.SelectOption(label="Paypal", description="Pay with Paypal", emoji="🟢"),
            discord.SelectOption(label="Cashapp", description="Pay with Cashapp", emoji="🔵"),
            discord.SelectOption(label="Giftcards", description="Pay with Giftcards", emoji="🔵")
        ]
        super().__init__(placeholder="Select your payment method", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        await interaction.response.send_message(f"You picked: {selected}", ephemeral=True)

# Step 2: Define the View that holds the dropdown
class DropdownView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MyDropdown())


def save_roles(roles):
    with open(CONFIG_FILE, "w") as f:
        for role_id in roles:
            f.write(str(role_id) + "\n")

def load_roles():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r") as f:
        lines = f.read().splitlines()
        return [int(r) for r in lines if r.strip().isdigit()]
    

class YesNoView(View):
    def __init__(self):
        super().__init__(timeout=None)  # 1 minute to respond
        self.value = None  # Save which button was clicked

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple)
    async def yes_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()  # acknowledge interaction

        # Send the next embed (customize this) TODO
        next_embed = discord.Embed(
            title="Next Step",
            description="You chose **Yes**. Here's the next embed!",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=next_embed)
        button.disabled = True
        self.stop()  # stop waiting for interaction

    @discord.ui.button(label="No", style=discord.ButtonStyle.blurple)
    async def no_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()  # acknowledge interaction

        # Close the ticket thread (delete the channel)
        if isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send("Ticket closed. Deleting thread...", ephemeral=True)
            await interaction.channel.delete()
        else:
            await interaction.followup.send("❌ This isn’t a thread. Nothing to close.", ephemeral=True)
        self.stop()




# --- Persistent Ticket Button ---
class TicketButton(Button):
    def __init__(self):
        super().__init__(label="🎟 Start Automatic Order", style=discord.ButtonStyle.green, custom_id="persistent_ticket_button")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        parent_channel = interaction.channel  # Where the button is clicked

        # Load staff role IDs
        role_ids = load_roles()

        # Check for existing ticket thread by name
        active_threads_list = await interaction.guild.active_threads()
        active_threads = [t for t in active_threads_list if t.parent_id == interaction.channel.id]
        if active_threads:
            await interaction.response.send_message("❗ You already have an open ticket here.", ephemeral=True)
            return

        # Create a private thread
        thread = await parent_channel.create_thread(
            name=f"ticket-{user.name}".lower(),
            type=discord.ChannelType.private_thread,
            invitable=True,
            auto_archive_duration=10080  # 24 hours, change as needed
        )

        # Add user to thread
        await thread.add_user(user)

        # Add all members of roles from config
        for role_id in role_ids:
            role = guild.get_role(role_id)
            if role:
                for member in role.members:
                    await thread.add_user(member)

        # Send welcome message with close button
        view = View(timeout=None)
        view.add_item(CloseTicketButton())
        await thread.send(f"{user.mention}, thank you for opening a ticket", view=view)
        embed = discord.Embed(
            title="**Would you like to start buying robux? (1/5)**",
            description="""Please click "Yes" if you would like to start purchasing your Robux.""",
            color=0xFFFFFF
        )
        f = YesNoView();
        await thread.send(embed=embed, view=f)
        await interaction.response.send_message(f"✅ Ticket thread created: {thread.mention}", ephemeral=True)

class CloseTicketButton(Button):
    def __init__(self):
        super().__init__(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="persistent_close_ticket_button")

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.Thread):
            await interaction.response.send_message("This command only works inside a ticket thread.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Closing and deleting your ticket...", ephemeral=True)
        await channel.delete()

# Persistent View to hold ticket button
class PersistentTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

# --- Slash commands for role config management ---

@bot.slash_command(description="Add a staff role to the ticket config")
async def addrole(ctx, role: discord.Role):
    roles = load_roles()
    if role.id in roles:
        await ctx.respond(f"Role `{role.name}` is already in the config.", ephemeral=True)
        return
    roles.append(role.id)
    save_roles(roles)
    await ctx.respond(f"Added role `{role.name}` to the ticket config.", ephemeral=True)

@bot.slash_command(description="Remove a staff role from the ticket config")
async def removerole(ctx, role: discord.Role):
    roles = load_roles()
    if role.id not in roles:
        await ctx.respond(f"Role `{role.name}` is not in the config.", ephemeral=True)
        return
    roles.remove(role.id)
    save_roles(roles)
    await ctx.respond(f"Removed role `{role.name}` from the ticket config.", ephemeral=True)

@bot.slash_command(description="View all staff roles in the ticket config")
async def viewconfig(ctx):
    role_ids = load_roles()
    if not role_ids:
        await ctx.respond("No roles are currently configured.", ephemeral=True)
        return

    guild = ctx.guild
    role_mentions = []
    for rid in role_ids:
        role = guild.get_role(rid)
        if role:
            role_mentions.append(role.mention)
        else:
            role_mentions.append(f"<@&{rid}>")
    await ctx.respond(f"Configured staff roles: {', '.join(role_mentions)}", ephemeral=True)

# --- Ticket command to send the ticket button ---

@bot.slash_command(description="Show the ticket creation button")
async def ticket(ctx):
    await ctx.defer()
    file = discord.File("robuxheaven3.gif", filename="robuxheaven3.gif")
    embed = discord.Embed(
        title="<:Robux:1383390534424334498> **Robux Automation**",
        description="""- This bot is a Discord bot designed to streamline the process of purchasing and distributing Robux, the virtual currency used in Roblox. \n
        **Instant Robux Delivery:**
        - Receive your Robux within moments of purchase. \n
        **Fully Automated Payments:**
        - Experience seamless transactions with our fully automated payment system. \n
        **Transaction Security:**
        - Our bot guarantees a safe and secure payment process every time. \n
        **Diverse Payment Options:**
        - Enjoy a variety of automated payment methods including Cryptocurrency, PayPal, and more! \n
        """,
        color=0xFFFFFF
    )
    embed.set_image(url="attachment://robuxheaven3.gif")
    view = PersistentTicketView()
    await ctx.followup.send(embed=embed, view=view, file=file)

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")
    bot.add_view(PersistentTicketView())  # This enables button after restart


bot.run('MTM5MzQwMTUxNjYzNDkzNTMxNw.GSm3iX.Q5YE7SDp1_EJoyfyIVhv3TtZ9rxZE_lJhNHLPw')