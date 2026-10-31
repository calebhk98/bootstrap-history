"""Where a crop run pays: the tiles an opening may place a producer on, and the yield its price is struck at.

A run of a recipe on a tile earns the recipe's revenue times the tile's yield factor and costs its variable cost
(`producers.plan` works a producer only where the first covers the second). The opening places a producer only
on a tile where that holds, so the year-1 plan is the runs the opening sized it for. The goods only such tiles
make are priced at the cost of the tiles that supply them (`supply_yield`), not at a yield no tile has. Plain
functions over built inputs."""
import math
from typing import Dict, List, Mapping, Optional

from . import unit_cost
from .types import GoodId, Recipe, TileId


FLOAT_SLACK = 1e-9     # relative width within which a revenue and a cost summed in different orders are the same number


def lowest_paying_yield(recipe: Recipe, prices: Mapping[GoodId, float], wages: Mapping[str, float]) -> float:
    """The yield factor at which a run's revenue equals its variable cost; 0 where either cannot be priced (the
    first year's plan then finds out, as it does for any run)."""
    variable = unit_cost.variable_cost_per_run(recipe, prices, wages)
    revenue = unit_cost.revenue_per_run(recipe, prices)
    if not (math.isfinite(variable) and variable > 0.0 and revenue > 0.0):
        return 0.0
    return variable / revenue


def pays(recipe: Recipe, yield_factor: float, prices: Mapping[GoodId, float], wages: Mapping[str, float]) -> bool:
    """Whether a run at a tile of this yield factor earns at least its variable cost, and the tile grows something."""
    return yield_factor > 0.0 and yield_factor * (1.0 + FLOAT_SLACK) >= lowest_paying_yield(recipe, prices, wages)


def sites(yield_by_tile: Mapping[TileId, float], recipe: Recipe, prices: Mapping[GoodId, float],
          wages: Mapping[str, float]) -> List[TileId]:
    """The tiles a recipe is placed on: those where a run pays; where none does, every tile that grows anything (a good
    never loses its last site: the first year's plan finds out), in id order."""
    kept = [tile for tile, factor in sorted(yield_by_tile.items()) if pays(recipe, factor, prices, wages)]
    return kept or [tile for tile, factor in sorted(yield_by_tile.items()) if factor > 0.0]


def paying(yield_by_tile: Mapping[TileId, float], floor: float) -> List[TileId]:
    """The tiles whose yield factor is at least `floor` (and above nothing), in id order."""
    return [tile for tile, factor in sorted(yield_by_tile.items()) if factor > 0.0 and factor >= floor]


def supply_yield(people_by_tile: Mapping[TileId, float], yield_by_tile: Mapping[TileId, float],
                 variable_share: float) -> Optional[float]:
    """The yield factor the goods of a crop are made at: the harmonic mean, weighted by people, of the tiles that pay
    at the price that mean implies. A price covering total cost at a mean yield `m` leaves a run on a tile paying only
    where its yield is at least `variable_share * m`; tiles under that drop out and the mean is taken again until
    none does. None where no tile grows anything."""
    growing: Dict[TileId, float] = {tile: factor for tile, factor in yield_by_tile.items()
                                    if factor > 0.0 and people_by_tile.get(tile, 0.0) > 0.0}
    share = min(max(variable_share, 0.0), 1.0)
    while growing:
        mean = (math.fsum(people_by_tile[tile] for tile in growing)
                / math.fsum(people_by_tile[tile] / factor for tile, factor in growing.items()))
        kept = {tile: factor for tile, factor in growing.items() if factor >= share * mean}
        if len(kept) == len(growing):
            return mean
        growing = kept
    return None
