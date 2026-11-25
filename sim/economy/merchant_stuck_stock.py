"""Stock a merchant holds for a route and cannot move (rule_sets.py).

A merchant keeps stock on a tile one of its routes starts from for carrying, and carrying takes crew hours hired at the
labour market, which only coin can hire. Under the search rules the stock is kept whole and every coin buys new cargo;
a merchant whose coin has gone into cargo then has stock it can neither carry nor sell. Under the clearing rules it
offers where it stands the part it cannot carry this year, for want of crew it hired or of room where the stock was
going, and the coin that carrying the rest will cost does not buy new cargo.

The part its crew can carry: under the search rules each stock takes the share of last year's carriage plan that was
hired on its tile, so a stock the hired hours cover whole is still cut, a part of every stock is offered where it stands
whenever a crew is a hair short of the plan, and the merchant buys none of a good where it offers it: it buys every
other year. Under the clearing rules the hours hired are set against the hours the stocks held need, crew key by crew
key, as the dispatch cuts its shipments (`merchants.dispatch`). Plain functions of built inputs."""
import math
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

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


Stock = Tuple[str, str]      # (good, the tile it stands on)


def hours_needed_by_stock(units_by_stock: Mapping[Stock, float], legs_by_stock: Mapping[Stock, Sequence[Leg]],
                          tonnes_per_unit: Mapping[str, float],
                          hours_per_tonne: Callable[[str, str], Iterable[Tuple[str, float]]]) -> Dict[Stock, Dict[str, float]]:
    """{stock: {crew key: hours}} to carry each stock held for a route along its legs (the units shared over them by
    weight, `merchants_legs.split`): its tonnes on a leg times the hours of each crew key a tonne of that haul needs
    (`hours_per_tonne(tile, destination tile)`). A leg that ends where the stock stands needs none, and a stock with no
    leg or no crew is left out."""
    needed: Dict[Stock, Dict[str, float]] = {}
    for stock in sorted(units_by_stock):
        legs = legs_by_stock.get(stock)
        if not legs:
            continue
        good, tile = stock
        for destination, _area, units in merchants_legs.split(legs, units_by_stock[stock]):
            if destination == tile or units <= 0.0:
                continue
            for key, hours in hours_per_tonne(tile, destination):
                by_key = needed.setdefault(stock, {})
                by_key[key] = by_key.get(key, 0.0) + units * tonnes_per_unit.get(good, 0.0) * hours
    return needed


def by_the_plans_share(stocks: Sequence[Stock], plan_share_by_tile: Mapping[str, float],
                       _hours_needed: Callable[[], Mapping[Stock, Mapping[str, float]]],
                       _hours_hired: Optional[Mapping[str, float]]) -> Dict[Stock, float]:
    """The share of each stock held for a route that its crew can carry: the share of the carriage plan hired on its
    tile (`crewed_share_by_tile`), the whole where the tile has no plan."""
    return {stock: plan_share_by_tile.get(stock[1], 1.0) for stock in stocks}


def by_the_hours_the_stocks_need(stocks: Sequence[Stock], _plan_share_by_tile: Mapping[str, float],
                                 hours_needed: Callable[[], Mapping[Stock, Mapping[str, float]]],
                                 hours_hired: Optional[Mapping[str, float]]) -> Dict[Stock, float]:
    """The share of each stock held for a route that its crew can carry: where the stocks together need more hours of a
    crew key than were hired of it, the share hired; a stock takes the least over the keys its haul needs, and the
    whole where none is short. The whole of every stock where there is no plan to hire for yet (`hours_hired` None:
    the first shipments are not held to a crew)."""
    if hours_hired is None:
        return {stock: 1.0 for stock in stocks}
    needed = hours_needed()
    totals: Dict[str, float] = {}
    for stock in sorted(needed):
        for key, hours in needed[stock].items():
            totals[key] = totals.get(key, 0.0) + hours
    cut = {key: max(0.0, hours_hired.get(key, 0.0)) / total for key, total in totals.items() if total > hours_hired.get(key, 0.0)}
    return {stock: min([cut[key] for key in needed.get(stock, {}) if key in cut], default=1.0) for stock in stocks}


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
