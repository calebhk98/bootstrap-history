"""Deterministic random draws for resource prospecting: every number comes from a sha256 of its labels.

No global random state and no Python `hash()`: the same (map, seed, tile, resource, deposit type,
index, label) always gives the same number, in any process, so a prospecting result can be
recomputed instead of stored. Also the truncated-lognormal expectation that matches the draws.
"""
import hashlib
import math
from statistics import NormalDist
from typing import Tuple

_NORMAL = NormalDist()
_POISSON_NORMAL_APPROXIMATION_ABOVE = 100.0


def uniform(*labels) -> float:
    """A number strictly between 0 and 1 fixed by the labels."""
    digest = hashlib.sha256("|".join(str(label) for label in labels).encode("utf-8")).digest()
    return (int.from_bytes(digest[:8], "big") + 0.5) / 2.0 ** 64


def standard_normal(*labels) -> float:
    return _NORMAL.inv_cdf(uniform(*labels))


def truncated_lognormal(median: float, sigma: float, limit_sigmas: float, *labels) -> float:
    """A lognormal draw whose standard-normal score is clipped at `limit_sigmas` above."""
    score = min(standard_normal(*labels), limit_sigmas)
    return median * math.exp(sigma * score)


def truncated_lognormal_mean(median: float, sigma: float, limit_sigmas: float) -> float:
    """Expected value of `truncated_lognormal`: the mean of a lognormal whose upper tail is clipped."""
    below = median * math.exp(sigma * sigma / 2.0) * _NORMAL.cdf(limit_sigmas - sigma)
    clipped = median * math.exp(sigma * limit_sigmas) * (1.0 - _NORMAL.cdf(limit_sigmas))
    return below + clipped


def overdispersed_count(expected: float, variance_to_mean: float, *labels) -> int:
    """A count with the given mean: Poisson whose rate carries a mean-one lognormal multiplier."""
    if expected <= 0.0:
        return 0
    extra = max(variance_to_mean - 1.0, 0.0)
    spread = math.sqrt(math.log(1.0 + extra / expected)) if extra > 0.0 else 0.0
    rate = expected * math.exp(spread * standard_normal(*labels, "rate") - spread * spread / 2.0)
    return poisson(rate, *labels, "count")


def poisson(rate: float, *labels) -> int:
    """Poisson draw by inversion of one uniform (normal approximation for large rates)."""
    point = uniform(*labels)
    if rate > _POISSON_NORMAL_APPROXIMATION_ABOVE:
        return max(0, int(round(rate + math.sqrt(rate) * _NORMAL.inv_cdf(point))))
    probability = math.exp(-rate)
    cumulative = probability
    count = 0
    while point > cumulative and count < 10000:
        count += 1
        probability *= rate / count
        cumulative += probability
    return count


def position_in_tile(lat: float, lon: float, area_km2: float, *labels) -> Tuple[float, float]:
    """A point uniformly inside a square of the tile's area centred on (lat, lon)."""
    half_side_km = math.sqrt(area_km2) / 2.0
    km_per_degree = 111.19
    north_km = (uniform(*labels, "north") - 0.5) * 2.0 * half_side_km
    east_km = (uniform(*labels, "east") - 0.5) * 2.0 * half_side_km
    cosine = max(math.cos(math.radians(lat)), 0.05)
    return lat + north_km / km_per_degree, lon + east_km / (km_per_degree * cosine)
