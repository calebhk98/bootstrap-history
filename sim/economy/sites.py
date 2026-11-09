"""Limits a site imposes on a recipe, handed in from outside; the economy models no deposit.

Geography owns deposits. It declares, per (recipe, tile), how many runs a year the site allows and at
what yield (`SiteLimit`), at the opening in the setup and each year in `EconomyYearInputs`; the economy keeps
producers inside those limits and reports what it worked (`extraction_by_tile`) so geography can deplete.
A site-bound recipe with any declared limit runs only on tiles that have one.
"""
import math
from typing import Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np
from sim.constants import declare

from . import producer_table
from .producer_rows import FLOAT_BIT

from .types import Recipe, SiteLimit, TileId

UNSITED_EXTRACTION_ANYWHERE = declare(
    "UNSITED_EXTRACTION_ANYWHERE", True, kind="temporary_heuristic",
    unit="flag: a site-bound recipe with no declared limit runs on any tile at its own yield", source=None,
    confidence="D",
    why="Until geography declares sites, a recipe that needs one is placed like any other and keeps its "
        "own yield. Which tiles hold what, and how much, is geography's to say, not the economy's.")

LimitsByRecipe = Dict[str, Dict[TileId, SiteLimit]]


def climate_allows(recipe: Recipe, tile_spec) -> bool:
    """Whether the tile's climate is one the recipe can be worked in (data names the climates; a recipe
    naming none, or a tile whose climate is not known, is allowed)."""
    classes = recipe.climate_classes
    climate = tile_spec.climate_class if tile_spec is not None else ""
    return not classes or not climate or climate in classes


def suited_tiles(recipe: Recipe, tile_specs, tiles: Sequence[TileId], runnable=None) -> Tuple[TileId, ...]:
    """The tiles whose climate allows the recipe and, when `runnable(recipe_id, tile)` is given, whose people can run it."""
    return tuple(tile for tile in tiles if climate_allows(recipe, tile_specs.get(tile))
                 and (runnable is None or runnable(recipe.recipe_id, tile)))


def limits_by_recipe(limits: Iterable[SiteLimit]) -> LimitsByRecipe:
    """The limits grouped by recipe, then tile (a later limit for the same pair replaces an earlier)."""
    grouped: LimitsByRecipe = {}
    for limit in limits:
        grouped.setdefault(limit.recipe_id, {})[limit.tile] = limit
    return grouped


def is_sited(recipe: Recipe, by_recipe: Mapping[str, Mapping[TileId, SiteLimit]]) -> bool:
    """True where the recipe is site-bound and has a declared limit somewhere."""
    return recipe.site_bound and bool(by_recipe.get(recipe.recipe_id))


def runs_anywhere(recipe: Recipe, by_recipe: Mapping[str, Mapping[TileId, SiteLimit]]) -> bool:
    """True where the recipe is site-bound with no declared limit and `UNSITED_EXTRACTION_ANYWHERE` lets it run on any tile."""
    return UNSITED_EXTRACTION_ANYWHERE and recipe.site_bound and not by_recipe.get(recipe.recipe_id)


def allowed_tiles(recipe: Recipe, by_recipe: Mapping[str, Mapping[TileId, SiteLimit]],
                  tiles: Sequence[TileId]) -> Tuple[TileId, ...]:
    """The tiles the recipe may run on: those with a limit when it is sited, else all of them."""
    if not is_sited(recipe, by_recipe):
        return tuple(tiles)
    return tuple(tile for tile in tiles if tile in by_recipe[recipe.recipe_id])


def headroom_runs(recipe: Recipe, tile: TileId, by_recipe: Mapping[str, Mapping[TileId, SiteLimit]],
                  capacity_there: float) -> float:
    """Runs of capacity the site still allows beyond `capacity_there`; unbounded where it is not sited."""
    if not is_sited(recipe, by_recipe):
        return math.inf
    limit = by_recipe[recipe.recipe_id].get(tile)
    return 0.0 if limit is None else max(0.0, limit.capacity_runs_per_year - capacity_there)


def yield_at(recipe: Recipe, tile: TileId, by_recipe: Mapping[str, Mapping[TileId, SiteLimit]],
             default: float = 1.0) -> float:
    limit = by_recipe.get(recipe.recipe_id, {}).get(tile) if recipe.site_bound else None
    return default if limit is None else limit.yield_factor


def apply_site_limits(record, setup) -> None:
    """Hold sited producers to the setup's limits: capacity capped (nil off a site), plant still to come cut to
    the room left, yield following the limit. The limits are looked up once per (recipe, tile) and the capacity and
    yield columns written for every sited producer at once."""
    by_recipe = limits_by_recipe(setup.site_limits)
    store = record.producers
    order = store.order()
    table = store.table
    sited = {number: is_sited(setup.recipes[name], by_recipe) if name in setup.recipes else False
             for number, name in enumerate(store.names["recipes"].name_list)}
    in_use = np.nonzero(np.array([sited[number] for number in table.recipe[order].tolist()], dtype=np.bool_))[0]
    if not len(in_use):
        return
    rows = order[in_use]
    recipe_names, tile_names = store.names["recipes"].name_list, store.names["tiles"].name_list
    limit_cap, limit_yield = np.full(len(rows), np.nan), np.zeros(len(rows))
    seen: Dict[Tuple[int, int], Tuple[float, float]] = {}
    for place, (recipe, tile) in enumerate(zip(table.recipe[rows].tolist(), table.tile[rows].tolist())):
        if (recipe, tile) not in seen:
            limit = by_recipe[recipe_names[recipe]].get(tile_names[tile])
            seen[(recipe, tile)] = (np.nan, 0.0) if limit is None else (limit.capacity_runs_per_year, limit.yield_factor)
        limit_cap[place], limit_yield[place] = seen[(recipe, tile)]
    has_limit = ~np.isnan(limit_cap)
    capacity = np.where(has_limit, np.minimum(table.capacity_runs[rows], limit_cap), 0.0)
    held_capacity = table.capacity_runs[rows]
    typed = table.numpy_typed[rows]
    keeps_capacity = has_limit & (held_capacity <= limit_cap)          # `min` hands back the producer's own figure, whatever type it is
    yield_typed = (typed & FLOAT_BIT["yield_factor"]) != 0
    capacity_typed = (typed & FLOAT_BIT["capacity_runs"]) != 0
    producer_table.set_rows(store, "yield_factor", rows, np.where(has_limit, limit_yield, table.yield_factor[rows]), typed=yield_typed & ~has_limit)
    producer_table.set_rows(store, "capacity_runs", rows, capacity, typed=capacity_typed & keeps_capacity)
    expansion = record.credit.expansion_runs
    if expansion:
        for place in range(len(rows)):
            producer_id = store.ids[int(rows[place])]
            if expansion.get(producer_id, 0.0) > 0.0:
                record.credit.trim_expansion(producer_id, max(0.0, (limit_cap[place] if has_limit[place] else 0.0) - capacity[place]))


def in_id_order(producers):
    """Producers by id, so a float sum over them does not depend on the order the record was built in."""
    return (producer for _, producer in sorted(producers.items()))


def extraction_by_tile(record, setup) -> Dict[Tuple[str, TileId], float]:
    """Runs of each site-bound recipe worked last year on each tile, for geography to deplete by."""
    worked: Dict[Tuple[str, TileId], float] = {}
    store = record.producers
    order = store.order()
    recipe_names, tile_names = store.names["recipes"].name_list, store.names["tiles"].name_list
    site_bound = [(setup.recipes[name].site_bound if name in setup.recipes else False) for name in recipe_names]
    for recipe, tile, last_runs in zip(store.table.recipe[order].tolist(), store.table.tile[order].tolist(), store.floats("last_runs", order)):
        if site_bound[recipe]:
            key = (recipe_names[recipe], tile_names[tile])
            worked[key] = worked.get(key, 0.0) + max(0.0, last_runs)
    return dict(sorted(worked.items()))
