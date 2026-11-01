"""What a producer learns its demand from at the year's close."""
from typing import Callable, Dict, Iterable, Mapping, Tuple

# Stock left below this share of the year's sales counts as sold out (rounding in settlement leaves a hair).
SOLD_OUT_LEFT_SHARE = 1e-6


def demand_seen(sold: float, left: float, own_capacity: float, market_capacity: float, market_unmet: float) -> float:
    """Quantity a producer takes as the year's demand: what it sold, plus, when it sold out (stock left is a hair or
    nothing), its share of everything buyers in its market wanted and did not get. Sellers share the unmet demand by
    capacity (output a year the plant allows), not by what each happened to sell, so a seller that could not run
    (an input was short) still sees the buyers it turned away."""
    if market_unmet <= 0.0 or own_capacity <= 0.0 or market_capacity <= 0.0 or left > SOLD_OUT_LEFT_SHARE * sold:
        return sold
    return sold + min(1.0, own_capacity / market_capacity) * market_unmet


def market_capacities(sellers: Iterable[Tuple[str, Mapping[str, float], float]],
                      area_of: Callable[[str, str], str]) -> Dict[Tuple[str, str], float]:
    """Output a year the sellers' plants allow, by (good, area): `sellers` are (tile, output per run by good, runs of
    capacity times yield)."""
    total: Dict[Tuple[str, str], float] = {}
    for tile, outputs, runs in sellers:
        for good, per_run in outputs.items():
            key = (good, area_of(good, tile))
            total[key] = total.get(key, 0.0) + per_run * runs
    return total
