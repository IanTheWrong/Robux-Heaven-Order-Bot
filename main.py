import discord
from discord.ui import Button, View
from discord.ui import View, Select
import os
from discord.ext import commands
import asyncio

CONFIG_FILE = "config.txt"
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Needed to fetch role members
intents.message_content = True  # <- THIS IS CRITICAL

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Config save/load ---
class MyDropdown(Select):
    def __init__(self, amt):
        self.amt = amt
        options = [
            discord.SelectOption(label="Cryptocurrency", description="Pay with Cryptocurrency", emoji="<:Crypto:1383512528788914329> "),
            discord.SelectOption(label="Paypal", description="Pay with Paypal", emoji="<:PAYPAL:1383512533515632660>"),
            discord.SelectOption(label="Cashapp", description="Pay with Cashapp", emoji="<:CA_CashApp:1383514315046387934> "),
            discord.SelectOption(label="Giftcards", description="Pay with Giftcards", emoji="<:Steam:1383390569522266142> ")
        ]
        super().__init__(placeholder="Select your payment method", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        new_name = f"{selected}-{(self.amt / 1000)}"
        if isinstance(interaction.channel, discord.Thread):
            await interaction.channel.edit(name=new_name)
        self.disabled = True
        new_view = View()
        new_view.add_item(self)
        if(selected == "Cryptocurrency"):
          await interaction.channel.purge(limit=2)
          next_embed = discord.Embed(
              title="**Please select your preferred crypto (4/5)**",
              description="""You have selected **Cryptocurrency** as your sending payment, What crypto will you be sending?""",
              color=0xFFFFFF
          )
          f = CryptocurrencyView(self.amt)
          await interaction.response.edit_message(embed=next_embed, view = f, wait=True)

          if(selected == "Paypal"):
            next_embed = discord.Embed(
                title="**Paypal Payment Invoice (5/5)**",
                description=f"""To ensure a smooth transaction process, we kindly request that all PayPal payments be sent through the **"Family and Friends"** option.\n**Payment Email**\nPing any staff available.\n**Payment Link**\nPing any staff available.\n**Amount USD**\n{self.amt/1000}""",
                color=0xFFFFFF
            )
            await interaction.response.edit_message(embed=next_embed, wait=True)
          if(selected == "Cashapp"):
            next_embed = discord.Embed(
                title="**Cashapp Payment Invoice (5/5)**",
                description=f"""To ensure a smooth transaction process, we kindly request that all PayPal payments be sent through the **Cashapp Balance** option.\n**Payment Tag**\nPing any staff available.\n**Payment Link**\nPing any staff available.\n**Amount USD**\n{self.amt/1000}""",
                color=0xFFFFFF
            )
            await interaction.response.edit_message(embed=next_embed, wait=True)

            
            
class CryptoDropdown(Select):
    def __init__(self, amt):
        self.amt = amt
        options = [
            discord.SelectOption(label="Bitcoin", description="BTC", emoji="<:bitcoin:1388867418289471559>"),
            discord.SelectOption(label="Litecoin", description="LTC", emoji="<:litecoin:1388867429710696559>"),
            discord.SelectOption(label="Ethereum", description="ETH", emoji="<:eth:1383512545670987958>"),
            discord.SelectOption(label="Solana", description="SOL", emoji="<:solana:1388867407472492616>")
        ]
        super().__init__(placeholder="Select the Crypto", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected = self.values[0]
        self.disabled = True
        new_view = View()
        new_view.add_item(self)
        if(selected == "Bitcoin"):
            print("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")

# Step 2: Define the View that holds the dropdown
class DropdownView(View):
    def __init__(self, amt):
        super().__init__(timeout=None)
        self.amt = amt
        self.add_item(MyDropdown(amt))
class CryptocurrencyView(View):
    def __init__(self, amt):
        super().__init__(timeout=None)
        self.amt = amt
        self.add_item(CryptoDropdown(amt))


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
    def __init__(self, bot):
        super().__init__(timeout=None)  # 1 minute to respond
        self.value = None  # Save which button was clicked
        self.bot = bot  # ✅ Store the bot instance

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple)
    async def yes_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()

        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        while True:
          # Send next embed
          next_embed = discord.Embed(
              title="**How much robux would you like to buy? (2/5)**",
              description="""Please specify the amount of Robux you would like to purchase:\nExample: **10,000**\nThe minimum order amount is: **10,000 Robux**""",
              color=0xFFFFFF
          )
          await interaction.followup.send(embed=next_embed, wait=True)

          def check(m):
              return m.author == interaction.user and m.channel == interaction.channel
          try:
              msg = await self.bot.wait_for("message", timeout=120, check=check)
              number = int(msg.content.strip().replace(",", ""))  # Extract digits & convert
              if number < 10000:
                  # Invalid amount, notify user and loop again
                  error_embed = discord.Embed(
                      title="Error",
                      description="❌ The amount must be at least 10,000 Robux. Please try again.",
                      color=0xFF0000
                  )
                  await interaction.channel.purge(limit=2)
                  await interaction.followup.send(embed=error_embed, ephemeral=True)
                  continue  # go back to asking for amount again
              else:
                  break  # valid input, exit loop
          except asyncio.TimeoutError:
              await interaction.followup.send("⏰ You didn't respond in time!", ephemeral=True)
          except ValueError:
              error_embed = discord.Embed(
                  title="**Error**",
                  description="Not a valid number.",
                  color=0xFF0000
              )
              await interaction.followup.send(embed=error_embed, ephemeral=True)
        confirm_embed = discord.Embed(
            title="**Would you like to purchase this amount of Robux (3/5)**",
            description=(
                f"Are you sure you want to purchase {number:,} Robux:\n"
                f"Current Rate **$1.0 per 1,000 Robux**\n"
                f"Price in USD: **${number / 1000:,.2f}**"
            ),
            color=0xFFFFFF
        )
        f = YesNoView2(bot, number);
        await interaction.followup.send(embed=confirm_embed,view = f, wait=True)


    @discord.ui.button(label="No", style=discord.ButtonStyle.blurple)
    async def no_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()  # acknowledge interaction
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Close the ticket thread (delete the channel)
        if isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send("Ticket closed. Deleting thread...", ephemeral=True)
            await interaction.channel.edit(archived=True, locked=True)
        else:
            await interaction.followup.send("❌ This isn’t a thread. Nothing to close.", ephemeral=True)
        self.stop()

class YesNoView2(View):
    def __init__(self, bot, number):
        super().__init__(timeout=None)  # 1 minute to respond
        self.value = None  # Save which button was clicked
        self.bot = bot  # ✅ Store the bot instance
        self.number = number

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.blurple)
    async def yes_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()

        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Send next embed
        next_embed = discord.Embed(
            title="**Please select your preferred payment method (4/5)**",
            description="""Please select your preferred payment method from the options provided below.""",
            color=0xFFFFFF
        )
        view = DropdownView(self.number)
        await interaction.followup.send(embed=next_embed, view = view, wait=True)



    @discord.ui.button(label="No", style=discord.ButtonStyle.blurple)
    async def no_button(self, button: Button, interaction: discord.Interaction):
        await interaction.response.defer()  # acknowledge interaction
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        await interaction.channel.purge(limit=3)
        next_embed = discord.Embed(
            title="**How much robux would you like to buy? (2/5)**",
            description="""Please specify the amount of Robux you would like to purchase:\nExample: **10,000**\nThe minimum order amount is: **10,000 Robux**""",
            color=0xFFFFFF
        )
        await interaction.followup.send(embed=next_embed, wait=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=120, check=check)
            number = int(msg.content.strip().replace(",", ""))  # Extract digits & convert

            confirm_embed = discord.Embed(
                title="**Would you like to purchase this amount of Robux (3/5)**",
                description=(
                    f"Are you sure you want to purchase {number:,} Robux:\n"
                    f"Current Rate **$1.0 per 1,000 Robux**\n"
                    f"Price in USD: **${number / 1000:,.2f}**"
                ),
                color=0xFFFFFF
            )
            f = YesNoView2(bot, number);
            await interaction.followup.send(embed=confirm_embed,view = f, wait=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ You didn't respond in time!", ephemeral=True)
        except ValueError:
            error_embed = discord.Embed(
                title="**Error**",
                description="Not a valid number.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

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
        f = YesNoView(bot);
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
        await channel.edit(archived=True, locked=True)

# Persistent View to hold ticket button
class PersistentTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

class PersistentCloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())

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
    bot.add_view(PersistentCloseTicketView())


bot.run('MTM5MzQwMTUxNjYzNDkzNTMxNw.GSm3iX.Q5YE7SDp1_EJoyfyIVhv3TtZ9rxZE_lJhNHLPw')