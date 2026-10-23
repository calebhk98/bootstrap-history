"""The land rent a newcomer expects on a site: the tile's rent in proportion to the newcomer's own use's value a
hectare (`land_market.use_rent_per_hectare`), not the tile's mean rent, which a use that earns a great deal from a hectare
(a mine) bids up for every other use."""
from typing import Mapping

from . import unit_cost
from .land_market import LandResult, use_rent_per_hectare
from .producers import Producer, expected_output_prices
from .types import TileId


def rent_per_run(rent_by_tile: Mapping[TileId, float], mean_value_by_tile: Mapping[TileId, float], tile: TileId,
                 land_per_run: float, revenue_per_run: float) -> float:
    """Rent on the land one run of the use takes on `tile`, the use earning `revenue_per_run` from that land."""
    if land_per_run <= 0.0:
        return 0.0
    posted = LandResult(dict(rent_by_tile), {}, dict(mean_value_by_tile))
    return use_rent_per_hectare(posted, tile, revenue_per_run / land_per_run) * land_per_run


def site_rent_per_run(setup, record, view, recipe_id: str, tile: TileId, yield_factor: float = 1.0) -> float:
    """Rent on a run of `recipe_id` on `tile` at the output prices a newcomer there expects, as the market now sees them."""
    recipe = setup.recipes[recipe_id]
    probe = Producer("probe", "probe", recipe_id, tile, 1.0)
    revenue = unit_cost.revenue_per_run(recipe, expected_output_prices(probe, recipe, view)) * yield_factor
    return rent_per_run(record.land_rent, record.land_mean_value, tile, setup.land_per_run.get(recipe_id, 0.0), revenue)
