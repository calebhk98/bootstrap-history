"""Stock a merchant holds for a route and cannot move (rule_sets.py).

A merchant keeps stock on a tile one of its routes starts from for carrying, and carrying takes crew hours hired at the
labour market, which only coin can hire. Under the search rules the stock is kept whole and every coin buys new cargo;
a merchant whose coin has gone into cargo then has stock it can neither carry nor sell. Under the clearing rules it
offers where it stands the part it cannot carry this year, for want of crew it hired or of room where the stock was
going, and the coin that carrying the rest will cost does not buy new cargo. Plain functions of built inputs."""
import math
from typing import Callable, Dict, Mapping, Sequence, Tuple

from . import merchants_legs

Leg = Tuple[str, str, float]


def crewed_share_by_tile(hours_wanted_by_key: Mapping[str, float], hours_hired_by_key: Mapping[str, float],
                         tile_of_key: Callable[[str], str]) -> Dict[str, float]:
    """Per source tile of a carriage plan, the share of the crew hours the plan wants there that was hired: the least
    over the tile's crew keys (the scarcest trade holds the haul), none to all. A tile the plan wants no hours for is
    left out."""
    shares: Dict[str, float] = {}
    for key, wanted in sorted(hours_wanted_by_key.items()):
        if wanted <= 0.0:
            continue
        share = min(1.0, max(0.0, hours_hired_by_key.get(key, 0.0)) / wanted)
        tile = tile_of_key(key)
        shares[tile] = min(shares.get(tile, 1.0), share)
    return shares


def kept_whole(_units_held: float, _share_crewed: float, _room_at_destinations: float) -> float:
    """Units of a stock held for a route that are offered where they stand: none, the stock waits for its haul."""
    return 0.0


def part_it_cannot_carry(units_held: float, share_crewed: float, room_at_destinations: float) -> float:
    """Units of a stock held for a route that are offered where they stand: what is left of it once the hired crew has
    carried its share and the destinations have taken what they have room for (the lesser of the two is carried)."""
    held = max(0.0, units_held)
    carried = min(held * min(1.0, max(0.0, share_crewed)), max(0.0, room_at_destinations))
    return held - carried


def carriage_set_aside(units_kept: float, carriage_per_unit_by_leg: Mapping[Tuple[str, str], float], legs: Sequence[Leg]) -> float:
    """The coin carrying `units_kept` of one stock will cost: the units shared over its route's legs by their weights
    (`merchants_legs.split`), each at its leg's carriage a unit (nothing for a leg with none named)."""
    if units_kept <= 0.0 or not legs:
        return 0.0
    return math.fsum(units * carriage_per_unit_by_leg.get((tile, area), 0.0) for tile, area, units in merchants_legs.split(legs, units_kept))


def all_cash(cash: float, _carriage_set_aside: float) -> float:
    """The coin that buys new cargo: all the merchant has."""
    return cash


def cash_less_carriage(cash: float, carriage_set_aside_for_kept_stock: float) -> float:
    """The coin that buys new cargo: what the merchant has less what carrying the stock it keeps will cost, never below nothing."""
    return max(0.0, cash - max(0.0, carriage_set_aside_for_kept_stock))
