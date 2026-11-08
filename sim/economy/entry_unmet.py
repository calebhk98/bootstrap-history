"""The entry plans for markets with unmet demand (`entry.entry_plans`) over the year arrays: the markets, their recipes and every recipe's
return are worked out as whole columns, the recipes of each market ranked by one sort, and `entry_unmet_kernel.unmet_plans` takes the
greedy loop. Python here only packs and unpacks (the `unmet_by_market` dictionary, the table of plans)."""
from typing import Dict, Tuple

import numpy as np

from . import entry_kernels, entry_plan_pack, entry_plan_table
from .entry import ENTRY_SHARE_OF_UNMET_DEMAND
from .entry_unmet_kernel import unmet_plans


def markets_of(costs, unmet_by_market: Dict[Tuple[str, str], float]):
    """(good column, area column) of the markets with a gap beyond the spare output of their makers, in (good, area) order, and the gap.
    A market whose good or area the area map does not know is left out."""
    keys = sorted(unmet_by_market)
    goods = np.array([costs.goods.row.get(good, -1) for good, _area in keys], dtype=np.int64)
    areas = np.array([costs.arrays.area_index.areas.row.get(area, -1) for _good, area in keys], dtype=np.int64)
    quantity = np.array([unmet_by_market[key] for key in keys], dtype=np.float64)
    anchors = entry_plan_pack.anchor_grid(costs)
    known = (goods >= 0) & (areas >= 0)
    known[known] = anchors[goods[known], areas[known]] >= 0
    spare = np.zeros(len(keys))
    spare[known] = costs.spare_output()[goods[known], areas[known]]
    gap = np.maximum(0.0, quantity - np.maximum(0.0, spare))
    wanted = known & (gap > 0.0)
    return goods[wanted], areas[wanted], gap[wanted]


def ranked_recipes(costs, goods: np.ndarray, areas: np.ndarray, gap: np.ndarray):
    """The recipes each market tries, in order: (market of each, recipe row, yearly return), best return first and recipe id breaking a
    tie, only recipes that make the good and beat the market's rate after the plant's wear (`entry.entry_plans`). Also the first
    position and the count of each market's recipes."""
    rate = costs.arrays.memory.rate[areas] if len(areas) else np.zeros(0)
    outputs = costs.matrices.outputs
    makes = (outputs[:, goods].T > 0.0) & ~np.isnan(rate)[:, None]
    market, recipe = np.nonzero(makes)
    runs = gap[market] / outputs[recipe, goods[market]] * ENTRY_SHARE_OF_UNMET_DEMAND
    for row in np.unique(recipe).tolist():
        costs._ensure_crew(row)
    anchors = entry_plan_pack.anchor_grid(costs)[goods[market], areas[market]]
    gross, after = entry_kernels.returns_many(recipe, anchors, runs, rate[market], costs.tables)
    keep = ~np.isnan(gross) & ~np.isnan(after) & (after > rate[market])
    market, recipe, gross = market[keep], recipe[keep], gross[keep]
    order = np.lexsort((recipe, -gross, market))
    market, recipe, gross = market[order], recipe[order], gross[order]
    count = np.bincount(market, minlength=len(goods)).astype(np.int64)
    first = np.concatenate(([0], np.cumsum(count)[:-1])).astype(np.int64) if len(goods) else np.zeros(0, dtype=np.int64)
    return recipe, gross, first, count


def unmet_plan_table(costs, block, unmet_by_market: Dict[Tuple[str, str], float]):
    """The `EntryPlans` table of the markets with unmet demand (`entry.entry_plans` with the year's tables and bids `block`, or None)."""
    goods, areas, gap = markets_of(costs, unmet_by_market)
    recipe, gross, first, count = ranked_recipes(costs, goods, areas, gap)
    plans = entry_plan_table.empty(len(recipe))
    if not len(goods):
        return plans
    index = costs.arrays.area_index
    anchors = entry_plan_pack.anchor_grid(costs)[goods, areas]
    places = entry_plan_pack.place_grid(costs, block)[goods, areas] if block is not None else np.full(len(goods), -1, dtype=np.int64)
    entry_plan_pack.site_tables(costs, recipe)
    made = unmet_plans(
        goods, anchors, gap, places, first, count, recipe, gross, entry_plan_pack.block_tuple(block), costs.tables, costs.own_rate,
        costs.matrices.outputs, costs.matrices.plant_goods, entry_plan_pack.sizing_tables(costs), costs.traded_grid(),
        entry_plan_pack.siting_state(costs), costs._site_tables, index.of_good_tile, plans)
    if made < 0:
        raise RuntimeError("the entry plan table was sized for one row per recipe tried and ran out")
    return plans
