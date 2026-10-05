"""Limits a site imposes on a recipe, handed in from outside; the economy models no deposit.

Geography owns deposits. It declares, per (recipe, tile), how many runs a year the site allows and at
what yield (`SiteLimit`), at the opening in the setup and each year in `YearInputs`; the economy keeps
producers inside those limits and reports what it worked (`extraction_by_tile`) so geography can deplete.
A site-bound recipe with any declared limit runs only on tiles that have one.
"""
import dataclasses
import math
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from sim.constants import declare

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
    climate = getattr(tile_spec, "climate_class", "") if tile_spec is not None else ""
    return not classes or not climate or climate in classes


def suited_tiles(recipe: Recipe, tile_specs, tiles: Sequence[TileId]) -> Tuple[TileId, ...]:
    return tuple(tile for tile in tiles if climate_allows(recipe, tile_specs.get(tile)))


def limits_by_recipe(limits: Iterable[SiteLimit]) -> LimitsByRecipe:
    """The limits grouped by recipe, then tile (a later limit for the same pair replaces an earlier)."""
    grouped: LimitsByRecipe = {}
    for limit in limits:
        grouped.setdefault(limit.recipe_id, {})[limit.tile] = limit
    return grouped


def is_sited(recipe: Recipe, by_recipe: Mapping[str, Mapping[TileId, SiteLimit]]) -> bool:
    """True where the recipe is site-bound and has a declared limit somewhere."""
    return recipe.site_bound and bool(by_recipe.get(recipe.recipe_id))


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


def apply_site_limits(record, setup, limits: Sequence[SiteLimit] = ()) -> None:
    """Hold sited producers to their limits: capacity capped (nil off a site), plant still to come cut to
    the room left, yield following the limit. Non-empty `limits` replace the setup's; empty keeps the last."""
    if limits:
        setup.site_limits = tuple(limits)
    by_recipe = limits_by_recipe(setup.site_limits)
    for producer_id, producer in sorted(record.producers.items()):
        recipe = setup.recipes.get(producer.recipe_id)
        if recipe is None or not is_sited(recipe, by_recipe):
            continue
        limit = by_recipe[recipe.recipe_id].get(producer.tile)
        capacity = min(producer.capacity_runs, limit.capacity_runs_per_year) if limit else 0.0
        record.producers[producer_id] = dataclasses.replace(
            producer, capacity_runs=capacity, yield_factor=limit.yield_factor if limit else producer.yield_factor)
        coming = record.expansion_runs.get(producer_id, 0.0)
        if coming > 0.0:
            room = max(0.0, (limit.capacity_runs_per_year if limit else 0.0) - capacity)
            if room > 0.0:
                record.expansion_runs[producer_id] = min(coming, room)
            else:
                del record.expansion_runs[producer_id]


def in_id_order(producers):
    """Producers by id, so a float sum over them does not depend on the order the record was built in."""
    return (producer for _, producer in sorted(producers.items()))


def extraction_by_tile(record, setup) -> Dict[Tuple[str, TileId], float]:
    """Runs of each site-bound recipe worked last year on each tile, for geography to deplete by."""
    worked: Dict[Tuple[str, TileId], float] = {}
    for producer in in_id_order(record.producers):
        recipe = setup.recipes.get(producer.recipe_id)
        if recipe is not None and recipe.site_bound:
            key = (producer.recipe_id, producer.tile)
            worked[key] = worked.get(key, 0.0) + max(0.0, producer.last_runs)
    return dict(sorted(worked.items()))
