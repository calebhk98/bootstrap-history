"""What siting a newcomer reads of the map and of the producers, as arrays (entry_tables.py asks for each once per year).

Each function is the loop of the same name's work in `EntryTables._ready_siting` / `_site_of` over records and dictionaries,
turned into a whole-table read; the answers are the loops' (same values, same order of every float sum):

    carriage_matrix        cost of a tonne from each tile (row) to each tile (column); infinity where no route runs. The costs a
                           carriage table searches are kept per table (they never change for a table; the year's wage scale is
                           applied on the way out, as `costs_from` applies it).
    hours_of_producers     the hours a run of each producer's recipe takes at its crew's practice, per producer row.
    land_short_rows        the rows of producers whose recipe takes land and whose ground was granted in part.
    yield_row, limit_row   a recipe's yield factor and its yearly capacity limit on each tile.
"""
import math
import weakref
from typing import Mapping, Sequence

import numpy as np

from . import practice
from .setup import RECIPE_TILE_SEPARATOR

_searched: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()      # carriage table -> (tile ids, unscaled cost matrix)


def _read_costs(carriage, tile_ids: Sequence[str], tile_row: Mapping[str, int], scaled: bool) -> np.ndarray:
    """The matrix from the table's per-source dictionaries (`unscaled_costs_from` when `scaled` is False)."""
    matrix = np.full((len(tile_ids), len(tile_ids)), np.inf)
    for source in tile_ids:
        if scaled:
            reached = carriage.costs_from(source) if hasattr(carriage, "costs_from") else {
                tile: carriage.cost_per_tonne(source, tile) for tile in tile_ids}
        else:
            reached = carriage.unscaled_costs_from(source)
        sources = matrix[tile_row[source]]
        for tile, cost in reached.items():
            column = tile_row.get(tile)
            if column is not None:
                sources[column] = cost
    return matrix


def carriage_matrix(carriage, tile_ids: Sequence[str], tile_row: Mapping[str, int]) -> np.ndarray:
    """The cost per tonne from each tile to each tile (infinity: no route). A carriage table that searches its costs once
    (`unscaled_costs_from`, `scale`) is read once per set of tiles and scaled here (an unreachable pair stays infinite)."""
    if not (hasattr(carriage, "unscaled_costs_from") and hasattr(carriage, "scale")):
        return _read_costs(carriage, tile_ids, tile_row, True)
    ids = tuple(tile_ids)
    try:
        kept = _searched.get(carriage)
    except TypeError:       # a table that cannot be weakly held is read again
        return _scaled(_read_costs(carriage, tile_ids, tile_row, False), carriage.scale)
    if kept is None or kept[0] != ids:
        kept = _searched[carriage] = (ids, _read_costs(carriage, tile_ids, tile_row, False))
    return _scaled(kept[1], carriage.scale)


def _scaled(unscaled: np.ndarray, scale: float) -> np.ndarray:
    """A copy of the cost matrix with every finite cost times `scale` (the matrix is written to by no one, but a kernel takes a
    writable array, so each build gets its own)."""
    if scale == 1.0:
        return unscaled.copy()
    return np.where(np.isfinite(unscaled), unscaled * scale, np.inf)


def hours_of_producers(recipes: Mapping[str, object], columns) -> np.ndarray:
    """Hours of labour a run takes for each producer row: the recipe's booked hours (summed exactly) at the practice its crew
    has, where it has one (`practice.recipe_for`)."""
    recipe_ids = columns.matrices.recipes.ids
    booked = np.zeros(len(recipe_ids))
    for row in np.unique(columns.recipe_row).tolist():
        booked[row] = math.fsum(recipes[recipe_ids[row]].labour_hours.values())
    hours = booked[columns.recipe_row]
    for position, producer in enumerate(columns.records):
        if producer.crew_runs:
            hours[position] = math.fsum(practice.recipe_for(recipes[producer.recipe_id], producer.crew_runs).labour_hours.values())
    return hours


def land_short_rows(columns, hectares_per_run_by_recipe_row: np.ndarray) -> np.ndarray:
    """Producer rows whose recipe takes land (`hectares_per_run_by_recipe_row` above zero) and whose `land_run_cap` is stated
    (location_land.land_short_tiles, over the columns)."""
    takes_land = hectares_per_run_by_recipe_row[columns.recipe_row] > 0.0
    return np.nonzero(takes_land & ~np.isnan(columns.land_run_cap))[0]


def yield_row(recipe, tile_ids: Sequence[str], factors: Mapping[str, float], limits: Mapping[str, object],
              tile_row: Mapping[str, int]) -> np.ndarray:
    """`sites.yield_at` of the recipe on each tile: the yield its limit on a tile states where it is site-bound, else the
    setup's factor for the recipe on that tile (one where none)."""
    prefix = recipe.recipe_id + RECIPE_TILE_SEPARATOR
    row = np.array([factors.get(prefix + tile, 1.0) for tile in tile_ids], dtype=np.float64)
    if recipe.site_bound:
        for tile, limit in limits.items():
            column = tile_row.get(tile)
            if column is not None:
                row[column] = limit.yield_factor
    return row


def limit_row(limits: Mapping[str, object], tile_ids: Sequence[str], tile_row: Mapping[str, int]) -> np.ndarray:
    """The yearly capacity a site-bound recipe's limit allows on each tile; none where it states no limit."""
    row = np.zeros(len(tile_ids))
    for tile, limit in limits.items():
        column = tile_row.get(tile)
        if column is not None:
            row[column] = limit.capacity_runs_per_year
    return row
