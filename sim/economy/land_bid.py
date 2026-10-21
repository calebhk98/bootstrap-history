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
from typing import Mapping, Optional, Sequence, Tuple

from . import titles_ground, titles_value
from .types import AgentId, AreaId, Bid, GoodId, Recipe, TileId


def land_goods(specs: Mapping[GoodId, object], recipes: Mapping[str, Recipe]) -> Tuple[GoodId, ...]:
    """Goods that are ground: immobile units that a recipe makes from nothing (no inputs, no hours)."""
    return tuple(sorted({good for recipe in recipes.values() if not recipe.inputs and not recipe.labour_hours
                         for good in recipe.outputs if good in specs and not specs[good].portable}))


def hours_per_hectare(recipe: Recipe, land_per_run: float) -> float:
    """Hours the recipe takes on one hectare-year."""
    return math.fsum(recipe.labour_hours.values()) / land_per_run if land_per_run > 0.0 else 0.0


def crop_margin_per_hectare(recipe: Recipe, land_per_run: float, fertility: float,
                            output_prices: Mapping[GoodId, float], wage_per_hour: float) -> float:
    """What a hectare-year of the recipe nets: its outputs at their prices (cut by the tile's fertility) less
    the hours it takes at the wage."""
    if land_per_run <= 0.0:
        return 0.0
    revenue = fertility * math.fsum(output_prices.get(good, 0.0) * quantity for good, quantity in recipe.outputs.items())
    return (revenue - wage_per_hour * math.fsum(recipe.labour_hours.values())) / land_per_run


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


def owners_of_sellers(record, recipes: Mapping[str, Recipe], good: GoodId, tile: TileId) -> Sequence[AgentId]:
    """The owners of the producers that make `good` on `tile`: whose land a sold hectare is."""
    return sorted({producer.owner for producer in record.producers.values()
                   if producer.tile == tile and good in recipes[producer.recipe_id].outputs})
