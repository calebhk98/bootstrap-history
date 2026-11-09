"""The buyer of cleared ground (Complaint 538): what a hectare is worth to an actor that would farm it, and the
bid and the title that follow. Plain functions of the actor's figures; any actor with hands to spare can use them.

A hectare earns its holder the better of the crop margin on it (what the recipe's output fetches at the prices
the actor sees, less its hours at the wage) and the tile's rent (what it pays as a tenant or would get by
letting it). It is worth that earning capitalised at the rate (titles_value.hectare_value), and the actor bids
no more than that for it, and only for the hectares its spare hours can work. Cleared ground is new arable land: a
hectare an actor takes up, bought or drawn from its own clearer's stock, is added to the tile's arable land and
becomes that actor's title (titles_ground.add_ground); no other holder gives up a hectare.
"""
import math
from typing import Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import titles_ground, titles_value, unit_cost
from .types import AgentId, AreaId, Bid, GoodId, Recipe, TileId, TradeId


def land_goods(specs: Mapping[GoodId, object], recipes: Mapping[str, Recipe]) -> Tuple[GoodId, ...]:
    """Goods that are ground: immobile units that a recipe makes from nothing (no inputs, no hours)."""
    return tuple(sorted({good for recipe in recipes.values() if not recipe.inputs and not recipe.labour_hours
                         for good in recipe.outputs if good in specs and not specs[good].portable}))


def hours_per_hectare(recipe: Recipe, land_per_run: float) -> float:
    """Hours the recipe takes on one hectare-year."""
    return math.fsum(recipe.labour_hours.values()) / land_per_run if land_per_run > 0.0 else 0.0


def crop_margin_per_hectare(recipe: Recipe, land_per_run: float, fertility: float,
                            output_prices: Mapping[GoodId, float], wages: Mapping[TradeId, float]) -> float:
    """What a hectare-year of the recipe nets: its outputs at their prices (cut by the tile's fertility) less
    the hours it takes, each trade's hours at that trade's wage (a trade with no wage makes the margin -inf). Every output must have a price (the caller leaves out a recipe whose output has none)."""
    if land_per_run <= 0.0:
        return 0.0
    revenue = fertility * math.fsum(output_prices[good] * quantity for good, quantity in recipe.outputs.items())
    return (revenue - unit_cost.labour_cost_per_run(recipe, wages)) / land_per_run


def earning_per_hectare(crop_margin: float, rent_per_hectare: float) -> float:
    """What a hectare earns its holder: the better of farming it and the rent on it, never below nothing."""
    return max(0.0, crop_margin, rent_per_hectare)


def workable_hectares(spare_hours: float, hours_on_a_hectare: float) -> float:
    """The hectares the actor's unused hours can work; with no crop to work (it would only let the ground for its
    rent) no hands limit it."""
    return max(0.0, spare_hours) / hours_on_a_hectare if hours_on_a_hectare > 0.0 else math.inf


def hectare_bid(buyer: AgentId, good: GoodId, area: AreaId, tile: TileId, earning: float, going_price: Optional[float],
                rate: float, hectares: float, cash: float) -> Optional[Bid]:
    """A bid for ground at no more than its capitalised earning, none unless that beats the going price, for no
    more hectares than its cash buys at that price."""
    worth = titles_value.hectare_value(earning, rate)
    hectares = min(hectares, cash / going_price) if going_price and going_price > 0.0 else 0.0     # no more than its cash buys
    if hectares <= 0.0 or cash <= 0.0 or not going_price or going_price <= 0.0 or worth <= going_price:
        return None
    return Bid(buyer, good, area, tile, 0.0, hectares, going_price, 0.0, min(cash, hectares * worth), 1,
               maximum_price=worth)


def take_up(record, receiver: AgentId, tile_id: TileId, hectares: float, arable_hectares: float) -> float:
    """Cleared ground the receiver holds becomes its title: new arable land on the tile (titles_ground.add_ground),
    not a share of anyone's. Returns the hectares added."""
    return titles_ground.add_ground(record, tile_id, receiver, hectares, arable_hectares)


def own_use(stock: float, hectares_needed: float, hectares_held: float) -> float:
    """The hectares a clearer's owner keeps from the clearer's own stock to farm itself: what its own plots need
    beyond the land it holds, no more than the stock. Nothing is sold of what it keeps."""
    return max(0.0, min(stock, hectares_needed - hectares_held))


_seller_indexes: Dict[int, tuple] = {}      # id of a producers table -> (table, stamp, (good, tile) -> owners)


def seller_index(record, recipes: Mapping[str, Recipe]) -> Dict[Tuple[GoodId, TileId], set]:
    """The owners of the producers that make each good on each tile, built once a year per producers table (producers are
    added and handed to new owners only when the year closes)."""
    producers = record.producers
    stamp = (len(producers), getattr(getattr(record, "memory", None), "year", None), id(recipes))
    kept = _seller_indexes.get(id(producers))
    if kept is None or kept[0] is not producers or kept[1] != stamp:
        index: Dict[Tuple[GoodId, TileId], set] = {}
        recipe_names, tile_names, owner_names = (producers.names[kind].name_list for kind in ("recipes", "tiles", "owners"))
        outputs = [recipes[name].outputs if name in recipes else None for name in recipe_names]
        live = np.array([each is not None for each in producers.ids], dtype=np.bool_)
        table = producers.table
        used = np.unique(table.recipe[:producers.count][live])
        if any(outputs[number] is None for number in used.tolist()):
            raise KeyError("a producer works a recipe the setup does not hold")
        for recipe, tile, owner in set(zip(table.recipe[:producers.count][live].tolist(), table.tile[:producers.count][live].tolist(),
                                           table.owner[:producers.count][live].tolist())):
            for good in outputs[recipe]:
                index.setdefault((good, tile_names[tile]), set()).add(owner_names[owner])
        _seller_indexes.clear()
        kept = _seller_indexes[id(producers)] = (producers, stamp, index)
    return kept[2]


def owners_of_sellers(record, recipes: Mapping[str, Recipe], good: GoodId, tile: TileId) -> Sequence[AgentId]:
    """The owners of the producers that make `good` on `tile`: whose land a sold hectare is."""
    return sorted(seller_index(record, recipes).get((good, tile), ()))
