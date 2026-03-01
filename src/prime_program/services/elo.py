from dataclasses import dataclass


@dataclass(frozen=True)
class EloOutcome:
    expected_score: float
    win_delta: float
    loss_delta: float


def expected_score(player_rating: int, opponent_rating: int, scale: int) -> float:
    return 1 / (1 + 10 ** ((opponent_rating - player_rating) / scale))


def calculate_elo_outcome(
    player_rating: int,
    opponent_rating: int,
    k_factor: int,
    scale: int,
) -> EloOutcome:
    expected = expected_score(player_rating=player_rating, opponent_rating=opponent_rating, scale=scale)
    return EloOutcome(
        expected_score=expected,
        win_delta=k_factor * (1 - expected),
        loss_delta=-(k_factor * expected),
    )
