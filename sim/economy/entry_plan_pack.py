"""What the entry plan kernels read, packed from the year arrays and the records once a phase: grids over (good, tile), (good, area) and
(recipe, tile) in place of the dictionary reads of `entry.py`, `entry_sizing.py`, `entry_year._traded_volume` and `EntryTables.siting`.

    traded_grid     units each good's market carried last year, seen from each tile; NaN for a good with no market (None there)
    anchor_grid     the anchor tile row of each (good, area), -1 where the good has no such area
    sizing_tables   the inputs each recipe cannot go ahead without (`entry_plan_steps.SizingTables`)
    place_grid      each (good, area)'s place in a year's bids block, -1 where it has none
    block_tuple     the bids block as the tuple the kernels read: six figure columns and `start`
    site_tables     what siting reads of each recipe, for the recipes asked for (`entry_plan_steps.SiteTables`)
    siting_state    the arrays siting reads and writes, as one tuple (the same arrays `EntryTables.siting` uses)
"""
from typing import Dict, Sequence

import numpy as np

from .entry_plan_steps import SITES, SIZING, SiteTables, SizingTables
from .year_arrays_memory import NO_AREA, market_cells

_sizing_kept: Dict[int, tuple] = {}       # id of the recipe matrices -> (matrices, sizing tables)
NOT_PLACED = -1


def traded_grid(costs) -> np.ndarray:
    """(good column, tile row): the units the good's market carried last year seen from the tile (`record.goods.volumes` of the
    market the tile is in), NaN for a good with no market. A market the memory does not number carries nothing."""
    arrays, record = costs.arrays, costs.record
    memory = record.memory
    good_rows, area_columns = market_cells(memory, costs.goods, arrays.area_index)
    carried = record.goods.volumes.take(np.arange(len(good_rows), dtype=np.int64))
    carried[np.isnan(carried)] = 0.0
    by_area = np.zeros((len(costs.goods.ids), max(1, len(arrays.area_index.areas.ids))))
    found = (good_rows >= 0) & (area_columns >= 0)
    by_area[good_rows[found], area_columns[found]] = carried[found]
    of_good_tile = arrays.area_index.of_good_tile
    grid = by_area[np.arange(len(costs.goods.ids))[:, None], np.maximum(of_good_tile, 0)]
    grid[of_good_tile == NO_AREA] = 0.0
    known = np.array([good in costs.known_goods for good in costs.goods.ids], dtype=np.bool_)
    grid[~known] = np.nan
    return grid


def anchor_grid(costs) -> np.ndarray:
    """(good column, area column): the row of the tile the market area is anchored on, -1 where the good has no such area. Kept on the
    area index while the area map and the arrays' numbering stand."""
    index = costs.arrays.area_index
    kept = index.stores.get("anchors")
    if kept is not None and kept[0] is costs.area_map and kept[1] is costs.goods and kept[2] is costs.tiles:
        return kept[3]
    grid = np.full((len(costs.goods.ids), max(1, len(index.areas.ids))), -1, dtype=np.int64)
    for good in costs.known_goods:
        good_column = costs.goods.row.get(good)
        if good_column is None:
            continue
        for area in costs.area_map.areas(good):
            area_column, tile_row = index.areas.row.get(area.area_id), costs.tiles.row.get(area.anchor_tile)
            if area_column is not None and tile_row is not None:
                grid[good_column, area_column] = tile_row
    index.stores["anchors"] = (costs.area_map, costs.goods, costs.tiles, grid)
    return grid


def sizing_tables(costs):
    """The `SizingTables` of the year's recipes (read once per set of recipe matrices)."""
    matrices = costs.matrices
    kept = _sizing_kept.get(id(matrices))
    if kept is not None and kept[0] is matrices:
        return kept[1]
    table = SIZING.new_table(SizingTables, len(matrices.recipes.ids), len(matrices.recipes.ids),
                             widths={"hard_inputs": len(matrices.goods.ids)})
    for row, recipe_id in enumerate(matrices.recipes.ids):
        for good, per_run in costs.setup.recipes[recipe_id].hard_inputs.items():
            table.hard_inputs[row, matrices.goods.row[good]] = per_run
    _sizing_kept.clear()
    _sizing_kept[id(matrices)] = (matrices, table)
    return table


def block_cells(costs, block):
    """(good column, area column) of each market of the bids `block`, -1 where the year arrays do not hold the good or the area. Kept on the
    block."""
    kept = getattr(block, "_cells", None)
    index = costs.arrays.area_index
    if kept is not None and kept[0] is costs.goods and kept[1] is index.areas:
        return kept[2], kept[3]
    good = np.array([costs.goods.row.get(each, -1) for each, _area in block.markets], dtype=np.int64)
    area = np.array([index.areas.row.get(each, -1) for _good, each in block.markets], dtype=np.int64)
    block._cells = (costs.goods, index.areas, good, area)
    return good, area


def place_grid(costs, block) -> np.ndarray:
    """(good column, area column): the place of the market in the bids `block`, -1 where it has none."""
    good, area = block_cells(costs, block)
    grid = np.full((len(costs.goods.ids), max(1, len(costs.arrays.area_index.areas.ids))), NOT_PLACED, dtype=np.int64)
    found = (good >= 0) & (area >= 0)
    grid[good[found], area[found]] = np.flatnonzero(found)
    return grid


def block_tuple(block) -> tuple:
    """The year's bids block as the kernels read it: floor, flexible, reference, elasticity, budget, maximum, start."""
    if block is None:
        return tuple(np.zeros(0) for _ in range(6)) + (np.zeros(1, dtype=np.int64),)
    return tuple(block.columns) + (block.start,)


def site_tables(costs, rows: Sequence[int]):
    """The `SiteTables` for every recipe row asked for so far (`rows` are added to those of earlier calls; worked out once per row).
    The tables are made on the first call and written in place after, so a kernel holding them sees later rows."""
    if not costs._siting_ready:
        costs._ready_siting()
    tables = getattr(costs, "_site_tables", None)
    recipes, tiles = len(costs.matrices.recipes.ids), len(costs.tiles.ids)
    if tables is None:
        tables = costs._site_tables = SITES.new_table(SiteTables, recipes, recipes, widths={
            "order": tiles, "fits": tiles, "suited": tiles, "supply_tiles": tiles})
        costs._site_rows = np.zeros(recipes, dtype=np.bool_)
    for row in sorted(set(int(each) for each in rows)):
        if costs._site_rows[row]:
            continue
        site = costs._site_of(row)
        tables.sited[row], tables.runs_anywhere[row] = site.sited, site.runs_anywhere
        tables.tonnes_out[row], tables.hours_per_run[row] = site.tonnes_out, site.hours_per_run
        tables.fits[row], tables.suited[row], tables.supply_tiles[row] = site.fits, site.suited, site.supply_tiles
        if site.order is not None:
            tables.order_count[row] = len(site.order)
            tables.order[row, :len(site.order)] = site.order
        costs._site_rows[row] = True
    return tables


def siting_state(costs) -> tuple:
    """The arrays siting reads and writes, in the order `entry_plan_steps.site_newcomer` takes them."""
    if not costs._siting_ready:
        costs._ready_siting()
    return (costs.input_tonnes, costs.supply_weight, costs.supply_present, costs.carriage_matrix, costs.hauls, costs.yield_rt, costs.limit_rt,
            costs.short_of_land, costs.hands_hours, costs.capacity, costs.committed)
