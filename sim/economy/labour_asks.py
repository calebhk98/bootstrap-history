"""Wages measured against what a worker of the trade asks: the family's subsistence per working hour,
plus the trade's danger pay and the pay that repays its training.

A labour market nobody offers hours in has no clearing wage; its remembered wage moves toward that ask,
the pay a worker would need to take the trade up, as an untraded good shows its cost of making
(notional.py). Workers drift toward trades that pay more over their ask than the tile's trades do on
average, up to the hands employers bid for, so a trade's premium is bounded by what training and danger
cost (a compensating differential), not by a thin market's luck.
"""
import math
from typing import Dict, Iterable, Mapping

from sim.constants import declare

from .labour import WAGE_ADJUSTMENT_SHARE_PER_YEAR, sticky_move

PAY_MOBILITY_SHARE_PER_YEAR = declare(
    "PAY_MOBILITY_SHARE_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of the room in a better-paid trade that workers fill in a year", source=None, confidence="D",
    why="People take up a trade that pays well over what its training and danger ask for, slowed by "
        "apprenticeship places, guilds and custom. How fast trades filled when their pay rose is not "
        "measured; stands in for the training model in sim/world/labour_market.py.")


def untraded_wages(wages: Mapping[str, float], offered_keys: Iterable[str],
                   asks: Mapping[str, float]) -> Dict[str, float]:
    """Remembered wages, those of markets nobody offered hours in moved toward the ask."""
    offered = set(offered_keys)
    moved = dict(wages)
    for key, ask in sorted(asks.items()):
        if key in moved and key not in offered and ask > 0.0:
            moved[key] = sticky_move(moved[key], ask, WAGE_ADJUSTMENT_SHARE_PER_YEAR)
    return moved


def follow_pay(workforce: Mapping[str, float], pay_over_ask: Mapping[str, float],
               wanted_workers: Mapping[str, float]) -> Dict[str, float]:
    """One tile's workers by trade after a year's moves toward trades paying more over their ask than the
    tile's workers earn on average: each draws a share of its unfilled posts, or of the hands its employers
    bid for when its posts are filled but its pay is still far over its ask."""
    working = {trade: count for trade, count in workforce.items() if count > 0.0 and trade in pay_over_ask}
    total = math.fsum(working.values())
    if total <= 0.0:
        return dict(workforce)
    average = math.fsum(count * pay_over_ask[trade] for trade, count in working.items()) / total
    arrivals: Dict[str, float] = {}
    for trade, ratio in sorted(pay_over_ask.items()):
        wanted = wanted_workers.get(trade, 0.0)
        # a trade paid far over its ask draws hands even with every post filled: the extra supply is what
        # brings its wage down to the ask, so a filled thin market cannot hold a runaway wage
        room = max(wanted - workforce.get(trade, 0.0), wanted * min(1.0, ratio / average - 1.0))
        if wanted > 0.0 and room > 0.0 and ratio > average:
            arrivals[trade] = PAY_MOBILITY_SHARE_PER_YEAR * room * min(1.0, ratio / average - 1.0)
    sources = {trade: count for trade, count in working.items() if pay_over_ask[trade] <= average}
    pool = math.fsum(sources.values())
    moving = min(math.fsum(arrivals.values()), PAY_MOBILITY_SHARE_PER_YEAR * pool)
    if moving <= 0.0:
        return dict(workforce)
    scale = moving / math.fsum(arrivals.values())
    moved = dict(workforce)
    for trade, count in sorted(sources.items()):
        moved[trade] -= moving * count / pool
    for trade, count in sorted(arrivals.items()):
        moved[trade] = moved.get(trade, 0.0) + count * scale
    return moved
