from dataclasses import dataclass

import disnake
from disnake.ext import commands

from prime_program.services.elo import calculate_elo_outcome
from prime_program.services.rank_points import infer_elite_points
from prime_program.settings import settings


def _format_signed(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


@dataclass(frozen=True)
class RivalProjection:
    index: int
    rank: int
    points: int
    expected_score: float
    win_delta: int
    loss_delta: int
    raw_win_delta: float
    raw_loss_delta: float

    @property
    def expected_pct(self) -> int:
        return round(self.expected_score * 100)


def _build_projection(index: int, my_points: int, rival_rank: int) -> RivalProjection:
    rival_points = infer_elite_points(rival_rank)
    outcome = calculate_elo_outcome(
        player_rating=my_points,
        opponent_rating=rival_points,
        k_factor=settings.elo_k_factor,
        scale=settings.elo_scale,
    )
    return RivalProjection(
        index=index,
        rank=rival_rank,
        points=rival_points,
        expected_score=outcome.expected_score,
        win_delta=round(outcome.win_delta),
        loss_delta=round(outcome.loss_delta),
        raw_win_delta=outcome.win_delta,
        raw_loss_delta=outcome.loss_delta,
    )


def _overview_table(rivals: list[RivalProjection]) -> str:
    headers = ("Rival", "Rank", "EP", "Exp", "Win", "Loss")
    rows: list[tuple[str, str, str, str, str, str]] = [
        (
            f"R{rival.index}",
            str(rival.rank),
            str(rival.points),
            f"{rival.expected_pct}%",
            _format_signed(rival.win_delta),
            _format_signed(rival.loss_delta),
        )
        for rival in rivals
    ]

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(row: tuple[str, str, str, str, str, str], is_header: bool = False) -> str:
        formatted = []
        for index, cell in enumerate(row):
            if index == 0 or is_header:
                formatted.append(cell.ljust(widths[index]))
            else:
                formatted.append(cell.rjust(widths[index]))
        return "  ".join(formatted)

    separator = "  ".join("-" * width for width in widths)
    return "\n".join([format_row(headers, is_header=True), separator, *(format_row(row) for row in rows)])


def _single_rival_embed(my_rank: int, my_points: int, rival: RivalProjection) -> disnake.Embed:
    color = (
        disnake.Color.from_rgb(44, 130, 201)
        if rival.expected_pct >= 50
        else disnake.Color.from_rgb(192, 57, 43)
    )
    embed = disnake.Embed(
        title="Single Elite Rival",
        description=(
            f"You: Rank **{my_rank}** (Elite Points **{my_points}**)\n"
            f"Rival: Rank **{rival.rank}** (Elite Points **{rival.points}**)"
        ),
        color=color,
        timestamp=disnake.utils.utcnow(),
    )
    embed.add_field(
        name="Expected",
        value=f"You're expected to win **{rival.expected_pct}%** of the time.",
        inline=False,
    )
    embed.add_field(name="If You Win", value=f"**{_format_signed(rival.win_delta)}** elite points", inline=True)
    embed.add_field(name="If You Lose", value=f"**{_format_signed(rival.loss_delta)}** elite points", inline=True)
    return embed


def _multi_rival_embed(my_rank: int, my_points: int, rivals: list[RivalProjection]) -> disnake.Embed:
    total_win = sum(rival.win_delta for rival in rivals)
    total_loss = sum(rival.loss_delta for rival in rivals)

    embed = disnake.Embed(
        title="Multiple Elite Rivals",
        description=f"You: Rank **{my_rank}** (Elite Points **{my_points}**)",
        color=disnake.Color.from_rgb(26, 188, 156),
        timestamp=disnake.utils.utcnow(),
    )

    table = _overview_table(rivals)
    embed.add_field(name="Overview", value=f"```{table}\n```", inline=False)
    embed.add_field(
        name="Totals Across All Rivals",
        value=(
            f"If you win against all: **{_format_signed(total_win)}**\n"
            f"If you lose against all: **{_format_signed(total_loss)}**"
        ),
        inline=False,
    )
    return embed


def _how_elo_works_embed() -> disnake.Embed:
    embed = disnake.Embed(
        title="How the ELO System Works",
        description="Your projected point changes are calculated in three steps:",
        color=disnake.Color.from_rgb(52, 73, 94),
        timestamp=disnake.utils.utcnow(),
    )
    embed.add_field(
        name="1) Convert Rank -> Elite Points",
        value=(
            "Ranks 1-16 use your manual point table.\n"
            "Missing values inside 1-16 are linearly interpolated.\n"
            "Ranks 17+ use `points = a - b * ln(rank)` with piecewise segments."
        ),
        inline=False,
    )
    embed.add_field(
        name="2) Expected Win Chance",
        value=(
            "`E = 1 / (1 + 10^((opponent_points - your_points) / scale))`\n"
            f"Current scale: **{settings.elo_scale}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="3) Point Change",
        value=(
            "`win_delta = K * (1 - E)`\n"
            "`loss_delta = -K * E`\n"
            f"Current K-factor: **{settings.elo_k_factor}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="Display Note",
        value="Command output rounds values to integers for readability.",
        inline=False,
    )
    return embed


class EliteHowItWorksView(disnake.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id

    @disnake.ui.button(label="How the ELO System Works", style=disnake.ButtonStyle.primary)
    async def how_elo_system_works(
        self,
        button: disnake.ui.Button,  # noqa: ARG002
        inter: disnake.MessageInteraction,
    ) -> None:
        if inter.author.id != self.owner_id:
            await inter.response.send_message("Only the command user can open this view.", ephemeral=True)
            return

        await inter.response.send_message(embed=_how_elo_works_embed(), ephemeral=True)


class EliteInsightsView(disnake.ui.View):
    def __init__(self, owner_id: int, my_rank: int, my_points: int, rivals: list[RivalProjection]):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.my_rank = my_rank
        self.my_points = my_points
        self.rivals = rivals

    @disnake.ui.button(label="Deeper Insights", style=disnake.ButtonStyle.secondary)
    async def deeper_insights(
        self,
        button: disnake.ui.Button,  # noqa: ARG002
        inter: disnake.MessageInteraction,
    ) -> None:
        if inter.author.id != self.owner_id:
            await inter.response.send_message("Only the command user can open this view.", ephemeral=True)
            return

        total_raw_win = sum(rival.raw_win_delta for rival in self.rivals)
        total_raw_loss = sum(rival.raw_loss_delta for rival in self.rivals)

        embed = disnake.Embed(
            title="Elite Check: Deeper Insights",
            description=f"You: Rank **{self.my_rank}** (Elite Points **{self.my_points}**)",
            color=disnake.Color.from_rgb(127, 140, 141),
            timestamp=disnake.utils.utcnow(),
        )

        for rival in self.rivals:
            rival_label = "Rival" if rival.index == 1 else f"Rival {rival.index}"
            embed.add_field(
                name=f"{rival_label} (Rank {rival.rank})",
                value=(
                    f"Elite points: **{rival.points}**\n"
                    f"Expected score: **{rival.expected_score:.4f}** ({rival.expected_pct}%)\n"
                    f"Raw win delta: **{rival.raw_win_delta:+.3f}**\n"
                    f"Raw loss delta: **{rival.raw_loss_delta:+.3f}**"
                ),
                inline=False,
            )

        embed.add_field(
            name="Model Info",
            value=(
                f"K-factor: **{settings.elo_k_factor}**\n"
                f"Scale: **{settings.elo_scale}**\n"
                f"Raw total win delta: **{total_raw_win:+.3f}**\n"
                f"Raw total loss delta: **{total_raw_loss:+.3f}**\n"
                "Displayed command values are rounded to integers."
            ),
            inline=False,
        )
        await inter.response.send_message(
            embed=embed,
            view=EliteHowItWorksView(owner_id=self.owner_id),
            ephemeral=True,
        )


class EliteCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name="elite_check",
        description="Check your ELO gain/loss against up to 4 rivals by rank.",
    )
    async def elite_check(
        self,
        inter: disnake.ApplicationCommandInteraction,
        my_rank: int = commands.Param(description="My Rank", ge=1),
        rival_rank: int = commands.Param(description="Rival Rank", ge=1),
        rival2_rank: int | None = commands.Param(default=None, description="Rival 2 Rank", ge=1),
        rival3_rank: int | None = commands.Param(default=None, description="Rival 3 Rank", ge=1),
        rival4_rank: int | None = commands.Param(default=None, description="Rival 4 Rank", ge=1),
    ) -> None:
        my_points = infer_elite_points(my_rank)
        rival_ranks = [rank for rank in (rival_rank, rival2_rank, rival3_rank, rival4_rank) if rank is not None]
        rivals = [_build_projection(index, my_points, rank) for index, rank in enumerate(rival_ranks, start=1)]
        view = EliteInsightsView(owner_id=inter.author.id, my_rank=my_rank, my_points=my_points, rivals=rivals)

        if len(rivals) == 1:
            await inter.response.send_message(embed=_single_rival_embed(my_rank, my_points, rivals[0]), view=view)
            return

        await inter.response.send_message(embed=_multi_rival_embed(my_rank, my_points, rivals), view=view)


def setup(bot: commands.InteractionBot) -> None:
    bot.add_cog(EliteCog(bot))
