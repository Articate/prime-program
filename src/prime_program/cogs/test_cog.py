"""
test_cog.py

Test cog for the /delete_score select-based flow.
Register with: bot.load_extension("test_cog")
"""

import disnake
from disnake.ext import commands

SCORES = [
    ("265 points", "101"),
    ("295 points", "102"),
    ("125 points", "103"),
    ("800 points", "104"),
]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


class DeleteScoreView(disnake.ui.View):
    """
    Presents the score list as a select menu, plus a Cancel button so the
    user can bail out before making a selection.
    """

    def __init__(self):
        super().__init__(timeout=60)

    @disnake.ui.string_select(
        placeholder="Choose a score to delete…",
        options=[disnake.SelectOption(label=label, value=value) for label, value in SCORES],
    )
    async def score_select(
        self,
        select: disnake.ui.StringSelect,
        inter: disnake.MessageInteraction,
    ):
        selected_value = select.values[0]
        selected_label = next(label for label, value in SCORES if value == selected_value)

        await inter.response.edit_message(
            content=f"⚠️ Are you sure you want to delete **{selected_label}**?",
            view=ConfirmDeleteView(score_id=selected_value, label=selected_label),
        )

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.secondary, row=1)
    async def cancel(
        self,
        button: disnake.ui.Button,
        inter: disnake.MessageInteraction,
    ):
        await inter.response.edit_message(content="Cancelled.", view=None)
        self.stop()


class ConfirmDeleteView(disnake.ui.View):
    """
    Shown after the user picks a score. Confirm deletes it, Cancel backs out.
    """

    def __init__(self, score_id: str, label: str):
        super().__init__(timeout=30)
        self.score_id = score_id
        self.label = label

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    @disnake.ui.button(label="Yes, delete it", style=disnake.ButtonStyle.danger)
    async def confirm(
        self,
        button: disnake.ui.Button,
        inter: disnake.MessageInteraction,
    ):
        # TODO: replace with real db.delete_score(self.score_id)
        print(f"[test] Deleting score id={self.score_id} ({self.label})")

        self._disable_all()
        await inter.response.edit_message(
            content=f"✅ **{self.label}** has been deleted.",
            view=self,
        )
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.secondary)
    async def cancel(
        self,
        button: disnake.ui.Button,
        inter: disnake.MessageInteraction,
    ):
        self._disable_all()
        await inter.response.edit_message(content="Cancelled.", view=self)
        self.stop()


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class TestCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command()
    async def delete_score(self, inter: disnake.ApplicationCommandInteraction):
        """Delete one of your submitted scores."""

        await inter.response.send_message(
            content="Select the score you want to delete:",
            view=DeleteScoreView(),
            ephemeral=True,
        )


def setup(bot: commands.InteractionBot):
    bot.add_cog(TestCog(bot))
