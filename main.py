import discord
from discord.ui import View, Button, Modal, InputText, Select
import os
from discord.ext import commands
import asyncio
import requests
import time
from dotenv import load_dotenv

CONFIG_FILE = "config.txt"
TARGET_CHANNEL_ID = 1383390323992039496
REVIEW_CHANNEL_ID = 1383390319785152533
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Needed to fetch role members
intents.message_content = True  # <- THIS IS CRITICAL
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!", intents=intents)

def usd_to_btc(usd_amount):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'usd'
    }
    response = requests.get(url, params=params)
    data = response.json()

    btc_price = data['bitcoin']['usd']  # current BTC price in USD
    btc_amount = usd_amount / btc_price
    return btc_amount

def usd_to_eth(usd):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {'ids': 'ethereum', 'vs_currencies': 'usd'}
    data = requests.get(url, params=params).json()
    price = data['ethereum']['usd']
    eth = usd / price
    return eth

def usd_to_ltc(usd):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {'ids': 'litecoin', 'vs_currencies': 'usd'}
    data = requests.get(url, params=params).json()
    price = data['litecoin']['usd']
    ltc = usd / price
    return ltc

def usd_to_sol(usd):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {'ids': 'solana', 'vs_currencies': 'usd'}
    data = requests.get(url, params=params).json()
    price = data['solana']['usd']
    sol = usd / price
    return sol

def create_order_embed(robux_purchased, rating, payment_method):
    # Emoji / icons for fields
    user_emoji = "👤"
    payment_emoji = "💳"
    robux_emoji = "🧱"
    usd_emoji = "💵"
    rating_emoji = "⭐"
    ticket_emoji = "📄"
    hidden_text = "Hidden (Anonymous)"
    payment_emoji2 = "<:booosters:1383390502107222036>"
    if(payment_method == "Paypal"):
        payment_emoji2 = "<:PAYPAL:1383512533515632660>"
    elif(payment_method == "Giftcards"):
        payment_emoji2 = "<:Steam:1383390569522266142>"
    elif(payment_method == "Ethereum (ETH)"):
        payment_emoji2 = "<:eth:1383512545670987958>"
    elif(payment_method == "Bitcoin (BTC)"):
        payment_emoji2 = "<:bitcoin:1388867418289471559>"
    elif(payment_method == "Litecoin (LTC)"):
        payment_emoji2 = "<:litecoin:1388867429710696559>"
    elif(payment_method == "Solana (SOL)"):
        payment_emoji2 = "<:solana:1388867407472492616>"
    elif(payment_method == "Cashapp"):
        payment_emoji2 = "<:CA_CashApp:1383514315046387934>"

    # Create star rating string (e.g., ★★★★★ for 5 stars)
    max_rating = 5
    filled_stars = "★" * rating
    empty_stars = "☆" * (max_rating - rating)
    rating_stars = f"{filled_stars}{empty_stars} ({rating}/5)"

    embed = discord.Embed(
        title="✅ New Completed Order",
        color=0xFFFFFF  # Green color
    )
    embed.set_thumbnail(url="attachment://robuxheaven3.gif")

    embed.add_field(name=f"{user_emoji} User", value=f"🔒 {hidden_text}", inline=True)
    embed.add_field(name=f"{payment_emoji} Payment Method", value=f"{payment_emoji2} {payment_method}", inline=True)

    embed.add_field(name=f"{robux_emoji} Robux Purchased", value=f"{robux_purchased:,} Robux", inline=False)
    embed.add_field(name=f"{usd_emoji} USD Spent", value=f"${robux_purchased/1000:,.2f}", inline=True)
    embed.add_field(name=f"{rating_emoji} Rating", value=rating_stars, inline=True)
    embed.add_field(name=f"{ticket_emoji} Ticket Order ID", value=str(int(time.time())), inline=False)

    embed.set_footer(text="Powered by Robux Heaven • discord.gg/robuxheaven")

    return embed
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
        await interaction.response.edit_message(view=new_view)
        if selected == "Cryptocurrency":
            await interaction.channel.purge(limit=2)
            embed = discord.Embed(
                title="**Crypto Selection (4/5)**",
                description="You selected **Cryptocurrency**. What crypto will you be sending?",
                color=0xFFFFFF
            )
            await interaction.followup.send(embed=embed, view=CryptocurrencyView(self.amt))

        elif selected == "Paypal":
            embed = discord.Embed(
                title="**Paypal Payment Invoice (5/5)**",
                description=f"""To ensure a smooth transaction process, we kindly request that all PayPal payments be sent through the **"Friends and Family"** option.\n
                **Payment Email**\nPing staff.\n
                **Payment Link**\nPing staff.\n
                **Amount USD**: ${self.amt / 1000:.2f}""",
                color=0xFFFFFF
            )
            await interaction.followup.send(embed=embed)

        elif selected == "Cashapp":
            embed = discord.Embed(
                title="**Cashapp Payment Invoice (5/5)**",
                description=f"""Please send payment using **CashApp Balance**.\n
                **Payment Tag**\nPing staff.\n
                **Payment Link**\nPing staff.\n
                **Amount USD**: ${self.amt / 1000:.2f}""",
                color=0xFFFFFF
            )
            await interaction.followup.send(embed=embed)
        elif selected == "Giftcards":
            embed = discord.Embed(
                title="**Giftcards Payment Method (5/5)**",
                description=f"To pay with giftcards, please ensure you purchase a giftcard that we **accept**. Make sure the gift card has the **required value**. After submitting the gift card information, please wait for our staff to verify it.",
                color=0xFFFFFF
            )
            embed.add_field(
                name="**Accepted Giftcards**",
                value="<:Rewarble:1383390562773630996>  Rewarble Giftcards (Recommended!), <:Steam:1383390569522266142>  Steam Giftcards or <:applepay:1383512540679770175>  Apple Giftcards. (USA ONLY!)",
                inline=False
            )
            embed.add_field(
                name="**Price in USD**",
                value=f"`{self.amt / 1000:.2f}`",
                inline=False
            )
            view = FormView()
            await interaction.followup.send(embed=embed, view = view)


class ApplicationForm(Modal):
    def __init__(self):
        super().__init__(title="Giftcard Information")

        self.add_item(InputText(label="Giftcard Type?", placeholder="Example: Steam Giftcard"))
        self.add_item(InputText(label="How Much $ Is In The Giftcard", placeholder="Example: 30$"))
        self.add_item(InputText(label="Additional Information", placeholder="It's an EU Steam Giftcard"))
        self.add_item(InputText(label="Giftcard Code", placeholder="000-000-000"))

    async def callback(self, interaction: discord.Interaction):
        # Format the result
        id = int(time.time())
        embed = discord.Embed(
            title="New Giftcard",
            color=0xFFFFFF
        )
        for item in self.children:
            embed.add_field(name=item.label, value=item.value, inline=False)
        embed.add_field(
            name = "ID",
            value = id,
            inline = False
        )
        embed.set_footer(text=f"Submitted by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        # Send to the configured channel
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel:
            await target_channel.send(embed=embed)
            embed = discord.Embed(
                title="Form Submitted",
                description=f"Your form was successfully submitted!\n**Form ID:** `{id}`",
                color=0xFFFFFF
            )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to send form. Channel not found.", ephemeral=True)

class FormView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit a Giftcard", style=discord.ButtonStyle.secondary)
    async def open_form(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplicationForm())

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
            embed = discord.Embed(
            title="**Bitcoin Payment Invoice (5/5)**",
            description=(
                f"This transaction is approximately **${self.amt / 1000:.2f}**, however to ensure we\n"
                "can validate your payment successfully please copy and paste the\n"
                f"value of **`{usd_to_btc(self.amt / 1000):.9f}`** and send it to our address."
            ),
            color=0xFFFFFF
            )

            embed.add_field(
                name="**Payment Address**",
                value="`bc1q63qum22rj4th2z66hdzj8qrmgghj6y55rsnj3x`",
                inline=False
            )

            embed.add_field(
                name="**Amount Bitcoin**",
                value=f"`{usd_to_btc(self.amt / 1000):.9f}`",
                inline=True
            )

            embed.add_field(
                name="**Amount USD**",
                value=f"`{self.amt / 1000:.2f}`",
                inline=True
            )

            file = discord.File("btc.png", filename="btc.png")
            embed.set_thumbnail(url="attachment://btc.png")

            await interaction.followup.send(embed=embed, file=file)

        elif(selected == "Litecoin"):
            embed = discord.Embed(
            title="**Litecoin Payment Invoice (5/5)**",
            description=(
                f"This transaction is approximately **${self.amt / 1000:.2f}**, however to ensure we\n"
                "can validate your payment successfully please copy and paste the\n"
                f"value of **`{usd_to_ltc(self.amt / 1000):.8f}`** and send it to our address."
            ),
            color=0xFFFFFF
        )

            embed.add_field(
                name="**Payment Address**",
                value="`LhLjjHNfgwHe7JxwQqGAtupmvpK2AdFMk2`",
                inline=False
            )

            embed.add_field(
                name="**Amount LTC**",
                value=f"`{usd_to_ltc(self.amt / 1000):.8f}`",
                inline=True
            )

            embed.add_field(
                name="**Amount USD**",
                value=f"`{self.amt / 1000:.2f}`",
                inline=True
            )

            file = discord.File("ltc.png", filename="ltc.png")
            embed.set_thumbnail(url="attachment://ltc.png")

            await interaction.followup.send(embed=embed, file=file)
        elif(selected == "Ethereum"):
            embed = discord.Embed(
            title="**Ethereum Payment Invoice (5/5)**",
            description=(
                f"This transaction is approximately **${self.amt / 1000:.2f}**, however to ensure we\n"
                "can validate your payment successfully please copy and paste the\n"
                f"value of **`{usd_to_eth(self.amt / 1000):.8f}`** and send it to our address."
            ),
            color=0xFFFFFF
        )

            embed.add_field(
                name="**Payment Address**",
                value="`0x5D49Fe71a87E7CD93E8d2e869109177f1e8d7E58`",
                inline=False
            )

            embed.add_field(
                name="**Amount ETH**",
                value=f"`{usd_to_eth(self.amt / 1000):.8f}`",
                inline=True
            )

            embed.add_field(
                name="**Amount USD**",
                value=f"`{self.amt / 1000:.2f}`",
                inline=True
            )

            file = discord.File("eth.png", filename="eth.png")
            embed.set_thumbnail(url="attachment://eth.png")

            await interaction.followup.send(embed=embed, file=file)
        elif(selected == "Solana"):
            embed = discord.Embed(
            title="**Solana Payment Invoice (5/5)**",
            description=(
                f"This transaction is approximately **${self.amt / 1000:.2f}**, however to ensure we\n"
                "can validate your payment successfully please copy and paste the\n"
                f"value of **`{usd_to_sol(self.amt / 1000):.6f}`** and send it to our address."
            ),
            color=0xFFFFFF
        )

            embed.add_field(
                name="**Payment Address**",
                value="`28Ch14NTPTwNKU5SFQnFGBGhUGkkTHiBteuiLczbmMWc`",
                inline=False
            )

            embed.add_field(
                name="**Amount SOL**",
                value=f"`{usd_to_sol(self.amt / 1000):.6f}`",
                inline=True
            )

            embed.add_field(
                name="**Amount USD**",
                value=f"`{self.amt / 1000:.2f}`",
                inline=True
            )

            file = discord.File("sol.png", filename="sol.png")
            embed.set_thumbnail(url="attachment://sol.png")

            await interaction.followup.send(embed=embed, file=file)


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

        # Get active threads under the current channel only
        active_threads = [
        t for t in interaction.channel.threads
        if not t.archived and t.owner_id == interaction.user.id
        ]

        if active_threads:
            await interaction.response.send_message("❗ You already have an open ticket in this channel.", ephemeral=True)
            return

        # Create a private thread
        thread = await parent_channel.create_thread(
            name=f"automatic-order-{user.name}".lower(),
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
        await thread.send(f"<@{277277385773023232}>{user.mention}, thank you for opening a ticket", view=view)
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

@bot.slash_command(description="Add a staff role to the ticket config",  default_member_permissions=discord.Permissions(administrator=True),dm_permission=False)
async def addrole(ctx, role: discord.Role):
    roles = load_roles()
    if role.id in roles:
        await ctx.respond(f"Role `{role.name}` is already in the config.", ephemeral=True)
        return
    roles.append(role.id)
    save_roles(roles)
    await ctx.respond(f"Added role `{role.name}` to the ticket config.", ephemeral=True)

@bot.slash_command(description="Remove a staff role from the ticket config", default_member_permissions=discord.Permissions(administrator=True),dm_permission=False)
async def removerole(ctx, role: discord.Role):
    roles = load_roles()
    if role.id not in roles:
        await ctx.respond(f"Role `{role.name}` is not in the config.", ephemeral=True)
        return
    roles.remove(role.id)
    save_roles(roles)
    await ctx.respond(f"Removed role `{role.name}` from the ticket config.", ephemeral=True)

@bot.slash_command(description="View all staff roles in the ticket config",  default_member_permissions=discord.Permissions(administrator=True),dm_permission=False)
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

@bot.slash_command(description="Show the ticket creation button", default_member_permissions=discord.Permissions(administrator=True),dm_permission=False)
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

@bot.slash_command(description="Write a Review",  default_member_permissions=discord.Permissions(administrator=True),dm_permission=False)
async def review(ctx, robux : int, rating : int, payment_method):
    file = discord.File("robuxheaven3.gif", filename="robuxheaven3.gif")
    embed = create_order_embed(robux,rating, payment_method)
    reviewChannel = bot.get_channel(REVIEW_CHANNEL_ID)
    await ctx.respond("Submitted", ephemeral = True)
    await reviewChannel.send(embed = embed, file = file)

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")
    bot.add_view(PersistentTicketView())  # This enables button after restart
    bot.add_view(PersistentCloseTicketView())


bot.run(TOKEN)