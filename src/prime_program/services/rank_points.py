from dataclasses import dataclass
from math import log

from prime_program.settings import settings

TOP_RANK_MAX = 16

# Keep this sparse/manual when needed. Missing ranks are interpolated between nearby anchors.
TOP_RANK_POINT_ANCHORS: dict[int, int] = {
    1: 2948,
    2: 2834,
    3: 2723,
    4: 2716,
    5: 2616,
    6: 2581,
    7: 2572,
    8: 2550,
    9: 2517,
    10: 2480,
    11: 2467,
    12: 2393,
    13: 2379,
    14: 2360,
    15: 2354,
    16: 2342,
    17: 2319,
    18: 2290,
    19: 2266,
    20: 2263,
}


@dataclass(frozen=True)
class LogLinearSegment:
    min_rank: int
    max_rank: int | None
    intercept: float
    slope: float

    def contains(self, rank: int) -> bool:
        return rank >= self.min_rank and (self.max_rank is None or rank <= self.max_rank)

    def points_at(self, rank: int) -> float:
        return self.intercept - self.slope * log(rank)


# P(r) ~= a - b * ln(r), split into configurable ranges.
LOG_LINEAR_SEGMENTS: tuple[LogLinearSegment, ...] = (
    LogLinearSegment(min_rank=17, max_rank=400, intercept=3475.612, slope=406.436),
    LogLinearSegment(min_rank=401, max_rank=None, intercept=4073.326, slope=510.422),
)


def _linear_interpolate(x: int, x1: int, y1: float, x2: int, y2: float) -> float:
    if x2 == x1:
        return y1
    return y1 + (y2 - y1) * ((x - x1) / (x2 - x1))


def _infer_top_rank_points(rank: int) -> float:
    anchors = dict(sorted(TOP_RANK_POINT_ANCHORS.items()))
    if not anchors:
        raise ValueError("Top-rank point anchors are empty.")

    exact = anchors.get(rank)
    if exact is not None:
        return exact

    lower_ranks = [value for value in anchors if value < rank]
    upper_ranks = [value for value in anchors if value > rank]

    if lower_ranks and upper_ranks:
        lower_rank = max(lower_ranks)
        upper_rank = min(upper_ranks)
        return _linear_interpolate(
            x=rank,
            x1=lower_rank,
            y1=anchors[lower_rank],
            x2=upper_rank,
            y2=anchors[upper_rank],
        )

    # If top-rank anchors are sparse and don't bracket this rank, fall back to the
    # log-linear model instead of extrapolating unstable top-rank values.
    return _infer_segment_points(rank)


def _infer_segment_points(rank: int) -> float:
    for segment in LOG_LINEAR_SEGMENTS:
        if segment.contains(rank):
            return segment.points_at(rank)
    raise ValueError(f"No log-linear segment covers rank {rank}.")


def _bottom_cliff(rank: int) -> float:
    r_top = settings.elite_bottom_cliff_top_rank
    r_max = settings.elite_bottom_cliff_max_rank
    p_top = settings.elite_bottom_cliff_top_points
    power = settings.elite_bottom_cliff_power

    if rank <= r_top:
        return float(p_top)
    if rank >= r_max:
        return 0.0

    t = (rank - r_top) / (r_max - r_top)
    return p_top * (1.0 - (t**power))


def infer_elite_points(rank: int) -> int:
    if rank <= 0:
        raise ValueError("Rank must be greater than 0.")

    if rank <= TOP_RANK_MAX:
        return round(_infer_top_rank_points(rank))

    if rank >= settings.elite_bottom_cliff_top_rank:
        return round(_bottom_cliff(rank))
    return round(_infer_segment_points(rank))
