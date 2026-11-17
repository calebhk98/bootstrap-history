"""What a producer learns its demand from at the year's close."""
from typing import Callable, Dict, Iterable, Mapping, Tuple

from sim.constants import declare

SOLD_OUT_LEFT_SHARE = declare(
    "SOLD_OUT_LEFT_SHARE", 0.01, kind="temporary_heuristic",
    unit="stock left, as a share of the year's sales, at which a seller no longer counts as sold out",
    source=None, confidence="D",
    retire="Complaints/643: a seller that knows which buyers it turned away needs no share of a market's unmet demand",
    why="A seller with nothing left turned buyers away and takes its share of the market's unmet demand as demand it "
        "missed; one with stock left did not. The share it takes falls in a straight line from all, with nothing left, "
        "to none at this share of its sales, so a hair of stock moves it by a hair (Complaint 473: at a rounding share "
        "the last digit decided). How much stock a seller that was sold out for most of the year still shows is not "
        "measured.")


def sold_out_weight(sold: float, left: float, sold_out_share: float = SOLD_OUT_LEFT_SHARE) -> float:
    """How far a seller counts as sold out, from one (nothing left) to nothing (stock left at `sold_out_share` of its sales or
    more), in a straight line between. A seller that sold nothing counts as sold out only with nothing left."""
    if left <= 0.0:
        return 1.0
    if sold <= 0.0:
        return 0.0
    return max(0.0, 1.0 - left / (sold_out_share * sold))


def demand_seen(sold: float, left: float, own_capacity: float, market_capacity: float, market_unmet: float) -> float:
    """Quantity a producer takes as the year's demand: what it sold, plus, as far as it sold out (`sold_out_weight`), its share
    of everything buyers in its market wanted and did not get. Sellers share the unmet demand by capacity (output a year the
    plant allows), not by what each happened to sell, so a seller that could not run (an input was short) still sees the
    buyers it turned away."""
    if market_unmet <= 0.0 or own_capacity <= 0.0 or market_capacity <= 0.0:
        return sold
    return sold + sold_out_weight(sold, left) * min(1.0, own_capacity / market_capacity) * market_unmet


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
