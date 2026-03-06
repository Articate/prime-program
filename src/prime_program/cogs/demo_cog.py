"""
demo_cog.py

A demonstration cog covering the main disnake slash command UX toolkit.
Register this cog in your bot with: bot.load_extension("demo_cog")

Commands included:
  /demo-embed       — Rich embed with all formatting features
  /demo-ephemeral   — Ephemeral (private) responses
  /demo-defer       — Deferred responses for slow work
  /demo-params      — Parameter types, constraints, and static choices
  /demo-autocomplete— Live autocomplete as the user types
  /demo-buttons     — Button styles, rows, and handling clicks
  /demo-select      — String select menu with multi-select
  /demo-modal       — Popup form with text inputs
  /demo-flow        — Full real-world flow: embed → buttons → modal → confirmation
"""

import asyncio

import disnake
from disnake.ext import commands

# ---------------------------------------------------------------------------
# Sample data used across demos
# ---------------------------------------------------------------------------

PLANETS = {
    "Mercury": {"diameter_km": 4_879, "moons": 0, "color": 0xB5B5B5},
    "Venus": {"diameter_km": 12_104, "moons": 0, "color": 0xE8C97A},
    "Earth": {"diameter_km": 12_742, "moons": 1, "color": 0x4FA3E0},
    "Mars": {"diameter_km": 6_779, "moons": 2, "color": 0xC1440E},
    "Jupiter": {"diameter_km": 139_820, "moons": 95, "color": 0xC88B3A},
    "Saturn": {"diameter_km": 116_460, "moons": 146, "color": 0xE4D191},
    "Uranus": {"diameter_km": 50_724, "moons": 28, "color": 0x7DE8E8},
    "Neptune": {"diameter_km": 49_244, "moons": 16, "color": 0x5B6FD6},
}

TOPPINGS = ["Pepperoni", "Mushrooms", "Onions", "Sausage", "Bell Peppers", "Olives", "Spinach", "Extra Cheese"]


# ---------------------------------------------------------------------------
# Reusable Views
# ---------------------------------------------------------------------------


class ButtonDemoView(disnake.ui.View):
    """
    Shows all five button styles across two rows.
    Clicking any enabled button sends an ephemeral reply and disables the
    whole view, so the user can't click again.
    """

    def __init__(self):
        super().__init__(timeout=60)

    async def _handle(self, inter: disnake.MessageInteraction, label: str):
        # Disable all buttons once one has been clicked
        for child in self.children:
            child.disabled = True

        await inter.response.edit_message(view=self)
        await inter.followup.send(f"You clicked **{label}**. All buttons are now disabled.", ephemeral=True)
        self.stop()

    async def on_timeout(self):
        # Disable all buttons when the view expires
        for child in self.children:
            child.disabled = True

    # --- Row 0 ---
    @disnake.ui.button(label="Primary", style=disnake.ButtonStyle.primary, row=0)
    async def primary(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._handle(inter, "Primary (blue)")

    @disnake.ui.button(label="Secondary", style=disnake.ButtonStyle.secondary, row=0)
    async def secondary(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._handle(inter, "Secondary (grey)")

    @disnake.ui.button(label="Success", style=disnake.ButtonStyle.success, row=0)
    async def success(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._handle(inter, "Success (green)")

    @disnake.ui.button(label="Danger", style=disnake.ButtonStyle.danger, row=0)
    async def danger(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._handle(inter, "Danger (red)")

    # --- Row 1 — a link button (no callback, opens URL) and a disabled button ---
    @disnake.ui.button(label="Link →", style=disnake.ButtonStyle.link, url="https://docs.disnake.dev", row=1)
    async def link(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass  # Link buttons never fire interactions

    @disnake.ui.button(label="Disabled", style=disnake.ButtonStyle.secondary, disabled=True, row=1)
    async def disabled_btn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass


class SelectDemoView(disnake.ui.View):
    """Single string select that allows picking 1–3 toppings."""

    def __init__(self):
        super().__init__(timeout=60)

    @disnake.ui.string_select(
        placeholder="Pick 1 to 3 toppings…",
        min_values=1,
        max_values=3,
        options=[disnake.SelectOption(label=t, value=t) for t in TOPPINGS],
    )
    async def topping_select(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction):
        chosen = ", ".join(select.values)

        # Disable the select after a choice is made
        select.disabled = True
        await inter.response.edit_message(view=self)

        await inter.followup.send(f"🍕 You selected: **{chosen}**", ephemeral=True)
        self.stop()


# ---------------------------------------------------------------------------
# Modal definitions
# ---------------------------------------------------------------------------


class FeedbackModal(disnake.ui.Modal):
    """
    A simple two-field modal: a short title and a longer description.
    Modals can have 1–5 TextInput components.
    """

    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Subject",
                placeholder="One-line summary…",
                custom_id="subject",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
            disnake.ui.TextInput(
                label="Details",
                placeholder="Describe your feedback in detail…",
                custom_id="details",
                style=disnake.TextInputStyle.paragraph,
                min_length=20,
                max_length=1000,
            ),
        ]
        super().__init__(title="Submit Feedback", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        subject = inter.text_values["subject"]
        details = inter.text_values["details"]

        embed = disnake.Embed(
            title="✅ Feedback Received",
            color=disnake.Color.green(),
        )
        embed.add_field(name="Subject", value=subject, inline=False)
        embed.add_field(name="Details", value=details, inline=False)
        embed.set_footer(text=f"From {inter.author.display_name}")

        await inter.response.send_message(embed=embed, ephemeral=True)


class OrderModal(disnake.ui.Modal):
    """Modal used in /demo-flow to collect special instructions."""

    def __init__(self, original_embed: disnake.Embed):
        self.original_embed = original_embed
        components = [
            disnake.ui.TextInput(
                label="Special Instructions",
                placeholder="e.g. Extra crispy, no onions…",
                custom_id="instructions",
                style=disnake.TextInputStyle.paragraph,
                required=False,
                max_length=300,
            ),
        ]
        super().__init__(title="Any special instructions?", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        instructions = inter.text_values["instructions"] or "None"

        # Update the original embed with the instructions and show confirmation
        self.original_embed.add_field(name="Special Instructions", value=instructions, inline=False)
        self.original_embed.color = disnake.Color.green()
        self.original_embed.title = "✅ Order Confirmed"

        await inter.response.edit_message(embed=self.original_embed, view=None)
        await inter.followup.send("Your order is on its way! 🎉", ephemeral=True)


class OrderFlowView(disnake.ui.View):
    """
    The view attached to the /demo-flow order summary.
    Three buttons: Confirm, Add Instructions (triggers modal), Cancel.
    """

    def __init__(self, embed: disnake.Embed):
        super().__init__(timeout=120)
        self.embed = embed

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    @disnake.ui.button(label="✅ Confirm Order", style=disnake.ButtonStyle.success)
    async def confirm(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self._disable_all()
        self.embed.color = disnake.Color.green()
        self.embed.title = "✅ Order Confirmed"
        await inter.response.edit_message(embed=self.embed, view=self)
        await inter.followup.send("Your order is on its way! 🎉", ephemeral=True)
        self.stop()

    @disnake.ui.button(label="📝 Special Instructions", style=disnake.ButtonStyle.primary)
    async def instructions(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # Responding to a button click with a modal is a common and clean pattern
        await inter.response.send_modal(OrderModal(self.embed))
        self.stop()

    @disnake.ui.button(label="❌ Cancel", style=disnake.ButtonStyle.danger)
    async def cancel(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self._disable_all()
        self.embed.color = disnake.Color.red()
        self.embed.title = "❌ Order Cancelled"
        await inter.response.edit_message(embed=self.embed, view=self)
        self.stop()


# ---------------------------------------------------------------------------
# The Cog
# ---------------------------------------------------------------------------


class DemoCog(commands.Cog):
    """Demonstrates disnake slash command features."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    # -----------------------------------------------------------------------
    # /demo-embed
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_embed(self, inter: disnake.ApplicationCommandInteraction):
        """Shows a rich embed with every available field type."""

        embed = disnake.Embed(
            title="🌍 Embed Demo",
            description=(
                "This embed demonstrates every section you can populate.\n"
                "Description supports **markdown**: *italics*, `code`, [links](https://disnake.dev)."
            ),
            color=disnake.Color.blurple(),
            url="https://docs.disnake.dev",  # Makes the title a hyperlink
        )

        # Author — appears above the title
        embed.set_author(
            name="Demo Bot",
            icon_url=inter.bot.user.display_avatar.url,
        )

        # Thumbnail — small image anchored top-right
        embed.set_thumbnail(url="https://i.imgur.com/8J0bkQw.png")

        # Fields — inline fields sit side by side (up to 3 per visual row)
        embed.add_field(name="Inline Field A", value="Left column", inline=True)
        embed.add_field(name="Inline Field B", value="Middle column", inline=True)
        embed.add_field(name="Inline Field C", value="Right column", inline=True)

        # A non-inline field always takes its own full row
        embed.add_field(
            name="Non-inline Field",
            value="This stretches across the full width of the embed.",
            inline=False,
        )

        # Large image at the bottom
        embed.set_image(url="https://i.imgur.com/2Y0VKXF.png")

        # Footer — small text and icon at the very bottom
        embed.set_footer(
            text=f"Requested by {inter.author.display_name}",
            icon_url=inter.author.display_avatar.url,
        )
        embed.timestamp = disnake.utils.utcnow()  # Appears next to the footer

        await inter.response.send_message(embed=embed)

    # -----------------------------------------------------------------------
    # /demo-ephemeral
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_ephemeral(self, inter: disnake.ApplicationCommandInteraction):
        """Sends two messages: one public, one only visible to you."""

        await inter.response.send_message("👋 This message is **public** — everyone in the channel can see it.")
        await inter.followup.send(
            "🔒 This followup is **ephemeral** — only you can see it.",
            ephemeral=True,
        )

    # -----------------------------------------------------------------------
    # /demo-defer
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_defer(self, inter: disnake.ApplicationCommandInteraction):
        """Defers the response, simulating slow work (e.g. an API call)."""

        # Defer immediately — Discord shows "Bot is thinking…"
        # ephemeral=True here means the eventual response is also ephemeral
        await inter.response.defer(ephemeral=False)

        # Simulate a slow operation
        await asyncio.sleep(3)

        embed = disnake.Embed(
            title="⏱️ Deferred Response",
            description=(
                "The bot deferred for 3 seconds before responding.\n"
                "Without deferring, interactions expire after **3 seconds**.\n"
                "After deferring, you have up to **15 minutes**."
            ),
            color=disnake.Color.orange(),
        )
        await inter.edit_original_response(embed=embed)

    # -----------------------------------------------------------------------
    # /demo-params
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_params(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(
            description="A plain text string (max 100 chars)",
            max_length=100,
        ),
        number: float = commands.Param(
            description="A number between 1 and 100",
            ge=1,
            le=100,  # Discord enforces these client-side
        ),
        planet: str = commands.Param(
            description="Pick a planet (static choices — no free text allowed)",
            choices=list(PLANETS.keys()),
        ),
        member: disnake.Member = commands.Param(
            description="A server member picker",
        ),
        visible: bool = commands.Param(
            default=True,
            description="Whether the response is public",
        ),
    ):
        """Demonstrates all major parameter types and constraints."""

        embed = disnake.Embed(title="📋 Parameter Demo", color=disnake.Color.teal())
        embed.add_field(name="Text (str)", value=text, inline=False)
        embed.add_field(name="Number (float)", value=str(number), inline=True)
        embed.add_field(name="Planet (choice)", value=planet, inline=True)
        embed.add_field(name="Member (User)", value=member.mention, inline=True)
        embed.add_field(name="Public (bool)", value=str(visible), inline=True)

        await inter.response.send_message(embed=embed, ephemeral=not visible)

    # -----------------------------------------------------------------------
    # /demo-autocomplete
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        planet: str = commands.Param(
            description="Start typing a planet name…",
            autocomplete=lambda inter, current: [p for p in PLANETS if current.lower() in p.lower()],
        ),
    ):
        """Suggests planet names as you type. Free text is still accepted — validated server-side."""

        data = PLANETS.get(planet)

        if data is None:
            await inter.response.send_message(
                f"❌ **{planet}** isn't a recognised planet. Try the suggestions!",
                ephemeral=True,
            )
            return

        embed = disnake.Embed(
            title=f"🪐 {planet}",
            color=data["color"],
        )
        embed.add_field(name="Diameter", value=f"{data['diameter_km']:,} km", inline=True)
        embed.add_field(name="Known Moons", value=str(data["moons"]), inline=True)

        await inter.response.send_message(embed=embed)

    # -----------------------------------------------------------------------
    # /demo-buttons
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_buttons(self, inter: disnake.ApplicationCommandInteraction):
        """Shows all five button styles across two rows. Click one to see it respond."""

        embed = disnake.Embed(
            title="🔘 Button Demo",
            description=(
                "Five button styles are available.\n"
                "- **Primary / Secondary / Success / Danger** fire interactions.\n"
                "- **Link** opens a URL and never fires an interaction.\n"
                "- Buttons can also be **disabled** (shown on row 2).\n\n"
                "Click any enabled button — they'll all disable afterwards."
            ),
            color=disnake.Color.blurple(),
        )

        await inter.response.send_message(embed=embed, view=ButtonDemoView())

    # -----------------------------------------------------------------------
    # /demo-select
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_select(self, inter: disnake.ApplicationCommandInteraction):
        """Shows a multi-select string dropdown (pick 1–3 pizza toppings)."""

        embed = disnake.Embed(
            title="🍕 Select Menu Demo",
            description=(
                "Select menus can enforce minimum and maximum selections.\n"
                "This one requires **1** and allows up to **3** choices.\n\n"
                "Pick your toppings below:"
            ),
            color=disnake.Color.red(),
        )

        await inter.response.send_message(embed=embed, view=SelectDemoView())

    # -----------------------------------------------------------------------
    # /demo-modal
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_modal(self, inter: disnake.ApplicationCommandInteraction):
        """Opens a modal (popup form) directly from a slash command."""

        # Responding with a modal is a special response type — you can only
        # send a modal as the *direct* response to an interaction.
        await inter.response.send_modal(FeedbackModal())

    # -----------------------------------------------------------------------
    # /demo-flow — ties everything together
    # -----------------------------------------------------------------------
    @commands.slash_command()
    async def demo_flow(
        self,
        inter: disnake.ApplicationCommandInteraction,
        size: str = commands.Param(
            description="Pizza size",
            choices=["Small (25cm)", "Medium (30cm)", "Large (35cm)"],
        ),
        pizza: str = commands.Param(
            description="Start typing a pizza name…",
            autocomplete=lambda inter, current: [
                p
                for p in ["Margherita", "Pepperoni", "BBQ Chicken", "Veggie Supreme", "Hawaiian", "Meat Feast"]
                if current.lower() in p.lower()
            ],
        ),
    ):
        """Full flow: autocomplete → embed → buttons → modal → edited confirmation."""

        embed = disnake.Embed(
            title="🍕 Order Summary",
            description="Review your order, then choose an action below.",
            color=disnake.Color.orange(),
        )
        embed.add_field(name="Pizza", value=pizza, inline=True)
        embed.add_field(name="Size", value=size, inline=True)
        embed.set_footer(text=f"Ordered by {inter.author.display_name}")
        embed.timestamp = disnake.utils.utcnow()

        await inter.response.send_message(
            embed=embed,
            view=OrderFlowView(embed),
        )


# ---------------------------------------------------------------------------
# Setup hook — required for load_extension()
# ---------------------------------------------------------------------------


def setup(bot: commands.InteractionBot):
    bot.add_cog(DemoCog(bot))
