import disnake
from disnake.ext import commands

from prime_program.services.elo import calculate_elo_outcome
from prime_program.settings import settings


class EliteCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name="elite_check",
        description="Check your ELO gain/loss against a rival.",
    )
    async def elite_check(
        self,
        inter: disnake.ApplicationCommandInteraction,
        my_rating: commands.Range[int, 1, ...],
        rival_rating: commands.Range[int, 1, ...],
    ) -> None:
        outcome = calculate_elo_outcome(
            player_rating=my_rating,
            opponent_rating=rival_rating,
            k_factor=settings.elo_k_factor,
            scale=settings.elo_scale,
        )

        await inter.response.send_message(
            "\n".join(
                [
                    f"Your rating: **{my_rating}**",
                    f"Rival rating: **{rival_rating}**",
                    f"Expected score: **{outcome.expected_score * 100:.0f}%**",
                    f"If you win: **+{outcome.win_delta:.0f}** points",
                    f"If you lose: **{outcome.loss_delta:.0f}** points",
                ]
            )
        )


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(EliteCog(bot))
