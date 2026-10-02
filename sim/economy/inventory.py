"""Stocks carried between years: what spoils, what wears out, and the price at which a holder lets go.

Pure functions over plain records. They return `GoodsMove` lists for the caller to book; nothing
here touches a ledger.
"""
from typing import Collection, List, Mapping, Optional, Tuple

from sim.constants import declare

from .types import EDGE_CONSUMPTION, EDGE_SPOILAGE, GoodId, GoodsMove, GoodSpec, TileId, is_edge

DEFAULT_MONTHS_OF_COVER = declare(
    "DEFAULT_MONTHS_OF_COVER", 3.0, kind="temporary_heuristic",
    unit="months of expected sales held as stock",
    source=None, confidence="D",
    why="A merchant or producer holds enough to serve sales until the next resupply or harvest. The "
        "real cover follows the carriage time, the harvest cycle and the cost of holding, which the "
        "economy does not yet derive; one value for every good until it does.")

DISTRESS_CURVE_EXPONENT = declare(
    "DISTRESS_CURVE_EXPONENT", 1.0, kind="temporary_heuristic",
    unit="dimensionless (power on the shortfall share of the stock's value)",
    source=None, confidence="D",
    why="A holder short of cash cuts its reservation price in proportion to how much of its stock's "
        "value it must raise, reaching any positive price when it must raise all of it. Only the "
        "endpoints are argued for; the straight line between them is a placeholder for a bargaining "
        "or fire-sale model.")

Holdings = Mapping[Tuple[str, GoodId, TileId], float]   # (agent, good, tile) -> quantity held


def _moves(holdings: Holdings, rate_of_good, receiver: str, purpose: str,
           users: Optional[Collection[str]]) -> List[GoodsMove]:
    moves = []
    for (agent, good, tile), quantity in sorted(holdings.items()):
        if is_edge(agent) or quantity <= 0.0 or (users is not None and agent not in users):
            continue
        lost = quantity * min(1.0, max(0.0, rate_of_good(good)))
        if lost > 0.0:
            moves.append(GoodsMove(agent, receiver, good, tile, lost, purpose))
    return moves


def spoilage_moves(holdings: Holdings, specs: Mapping[GoodId, GoodSpec]) -> List[GoodsMove]:
    """Each held stock loses its good's yearly spoilage share, to the spoilage edge account."""
    def rate(good):
        spec = specs.get(good)
        return spec.spoilage_per_year if spec else 0.0
    return _moves(holdings, rate, EDGE_SPOILAGE, "spoilage", None)


def wear_moves(holdings: Holdings, specs: Mapping[GoodId, GoodSpec],
               users: Collection[str]) -> List[GoodsMove]:
    """A durable in use loses one service life's worth a year. `users` are the agents that use their
    durables rather than trade them; a merchant's stock of the same good is not worn."""
    def rate(good):
        spec = specs.get(good)
        return 1.0 / spec.service_life_years if spec and spec.service_life_years > 0.0 else 0.0
    return _moves(holdings, rate, EDGE_CONSUMPTION, "wear", users)


def holding_reservation(expected_price: float, interest_rate: float, spoilage_per_year: float,
                        storage_cost_per_unit: float) -> float:
    """The lowest price at which a holder sells now: what carrying a unit to next year would net,
    discounted back a year. Below this it keeps the stock."""
    surviving = 1.0 - min(1.0, max(0.0, spoilage_per_year))
    return (expected_price * surviving - storage_cost_per_unit) / (1.0 + max(interest_rate, -0.99))


def distressed_reservation(normal_reservation: float, cash_shortfall: float,
                           stock_value_at_normal: float) -> float:
    """A reservation lowered as the cash the holder must raise grows against its stock's value; at
    a shortfall equal to the whole stock it is zero, which any positive price meets. A reservation
    already at or below zero (a waste product) is left alone."""
    if normal_reservation <= 0.0 or cash_shortfall <= 0.0:
        return normal_reservation
    if stock_value_at_normal <= 0.0:
        return 0.0
    share = min(1.0, cash_shortfall / stock_value_at_normal)
    return normal_reservation * (1.0 - share ** DISTRESS_CURVE_EXPONENT)


def target_stock(expected_yearly_sales: float, months_of_cover: Optional[float] = None) -> float:
    """The stock worth holding to serve expected sales for the months of cover."""
    cover = DEFAULT_MONTHS_OF_COVER if months_of_cover is None else months_of_cover
    return max(0.0, expected_yearly_sales) * max(0.0, cover) / 12.0
