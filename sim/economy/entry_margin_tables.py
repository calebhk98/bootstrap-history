"""The margin's and the trial's entry plans over the year arrays (`entry_margin.margin_entry_plans`, `entry_trial.trial_entry_plans`): the
markets with bids, their capacity and prices, and the recipes of each ranked by cost are worked out as whole columns, and
`entry_margin_kernel` takes the greedy loops. Python here only packs and unpacks (the saved `margin_years` streaks, the table of plans).

    weighed_markets   the block's markets whose good has makers and an area on the map (`entry_bid_markets.weigh` as columns)
    ranked_by_cost    every market's recipes cheapest first (`EntryTables.recipes_by_cost_many` as columns)
    margin_plan_table, trial_plan_table   the `EntryPlans` each rule makes
"""
import numpy as np

from . import entry_kernels, entry_plan_pack, entry_plan_table
from .entry_margin import MARGIN_ENTRY_GROWTH_SHARE, keep_streaks
from .entry_margin_kernel import margin_plans, trial_plans
from .entry_sizing import ENTRY_SHARE_OF_UNTRADED_DEMAND
from .entry_trial import ENTRY_PRICE_MARGIN_SHARE
from .market_memory import market_key
from .market_table_kernels import scatter_values
from .year_arrays_memory import market_cells


class Weighed:
    """The block's markets with makers and an area, in block order: `place` (row of the block), `good`, `area` (columns of the year arrays),
    `anchor` (tile row of the area's anchor), `capacity` (output the makers could reach, plant to come counted) and `price` (NaN: none)."""

    def __init__(self, costs, block):
        good, area = entry_plan_pack.block_cells(costs, block)
        makers = (costs.matrices.outputs > 0.0).any(axis=0)
        known = np.array([each in costs.known_goods for each in costs.goods.ids], dtype=np.bool_)
        present = (good >= 0) & (area >= 0)
        present[present] = known[good[present]] & makers[good[present]]
        anchors = entry_plan_pack.anchor_grid(costs)
        present[present] &= anchors[good[present], area[present]] >= 0
        self.place = np.flatnonzero(present)
        self.good, self.area = good[self.place], area[self.place]
        self.anchor = anchors[self.good, self.area]
        self.capacity = costs.reach_grid()[self.good, self.area]
        self.price = costs.arrays.memory.price[self.good, self.area]


def ranked_by_cost(costs, goods: np.ndarray, anchors: np.ndarray, output_per_year: np.ndarray):
    """The recipes that make each market's good, cheapest full cost per unit first (a recipe id breaking a tie), those that can be costed:
    (recipe row, cost, first position and count of each market). `output_per_year` (NaN for none) is what a newcomer would make a year, which
    sets the hours it is costed at."""
    outputs = costs.matrices.outputs
    market, recipe = np.nonzero(outputs[:, goods].T > 0.0)
    made = outputs[recipe, goods[market]]
    planned = ~np.isnan(output_per_year[market])
    runs = np.where(planned, output_per_year[market] / made, np.nan)
    for row in np.unique(recipe[planned]).tolist():
        costs._ensure_crew(row)
    cost = entry_kernels.full_costs(recipe, anchors[market], goods[market], runs, costs.own_rate, costs.tables)
    keep = np.isfinite(cost) & (cost > 0.0)
    market, recipe, cost = market[keep], recipe[keep], cost[keep]
    order = np.lexsort((recipe, cost, market))
    market, recipe, cost = market[order], recipe[order], cost[order]
    count = np.bincount(market, minlength=len(goods)).astype(np.int64)
    first = (np.cumsum(count) - count).astype(np.int64)
    return recipe, cost, first, count


def skipped_cells(costs, plans) -> np.ndarray:
    """(good column, area column) of the markets a plan of the table was drawn by (the area is the good's on the plan's tile)."""
    used = entry_plan_table.count(plans)
    index = costs.arrays.area_index
    grid = np.zeros((len(costs.goods.ids), max(1, len(index.areas.ids))), dtype=np.bool_)
    good, area = plans.good_col[:used], index.of_good_tile[plans.good_col[:used], plans.tile_row[:used]]
    grid[good[area >= 0], area[area >= 0]] = True
    return grid


def _streaks_in(costs, record) -> np.ndarray:
    """(good column, area column): the years in a row each market's expected price has stood above its entry price (`margin_years`)."""
    index = costs.arrays.area_index
    grid = np.zeros((len(costs.goods.ids), max(1, len(index.areas.ids))), dtype=np.int64)
    good_rows, area_columns = market_cells(record.memory, costs.goods, index)
    numbers = record.memory.tables.goods_markets.numbers
    kept = record.goods.margin_years
    rows = np.fromiter((numbers.get(key, -1) for key in kept), dtype=np.int64, count=len(kept))
    values = np.fromiter(kept.values(), dtype=np.int64, count=len(kept))
    found = (rows >= 0) & (rows < len(good_rows))
    found[found] = (good_rows[rows[found]] >= 0) & (area_columns[rows[found]] >= 0)
    grid[good_rows[rows[found]], area_columns[rows[found]]] = values[found]
    return grid


def _usual_prices(costs, record) -> np.ndarray:
    """(good column, area column): the market's usual (slow) price, NaN where it has none."""
    index = costs.arrays.area_index
    grid = np.full((len(costs.goods.ids), max(1, len(index.areas.ids))), np.nan)
    good_rows, area_columns = market_cells(record.memory, costs.goods, index)
    table = record.memory.tables.goods_table
    scatter_values(grid, table.usual_price, good_rows, area_columns, int(table.row_count[0]))
    return grid


def _write_streaks(costs, record, weighed: Weighed, years_out, counted) -> None:
    """The streaks the rule keeps are the markets it counted; any other market's streak starts again (`margin_years` in place)."""
    ids_good, ids_area = costs.goods.ids, costs.arrays.area_index.areas.ids
    keep = {}
    for position in np.flatnonzero(counted).tolist():
        keep[market_key(ids_good[weighed.good[position]], ids_area[weighed.area[position]])] = int(years_out[position])
    keep_streaks(record, keep)


def margin_plan_table(costs, record, block, weighed: Weighed, skipped: np.ndarray):
    """The `EntryPlans` of the margin rule over `weighed` (`Weighed`), with the streaks written to `record.goods.margin_years`."""
    index = costs.arrays.area_index
    chosen = np.flatnonzero((weighed.capacity > 0.0) & ~np.isnan(weighed.price))
    usual = _usual_prices(costs, record)[weighed.good[chosen], weighed.area[chosen]]
    price = weighed.price[chosen]
    expected = np.where(np.isnan(usual), price, usual)
    recipe, cost, first, count = ranked_by_cost(costs, weighed.good[chosen], weighed.anchor[chosen], MARGIN_ENTRY_GROWTH_SHARE * weighed.capacity[chosen])
    plans = entry_plan_table.empty(len(recipe))
    years_out = np.zeros(len(chosen), dtype=np.int64)
    counted = np.zeros(len(chosen), dtype=np.bool_)
    if len(chosen):
        entry_plan_pack.site_tables(costs, recipe)
        made = margin_plans(
            weighed.good[chosen], weighed.anchor[chosen], weighed.place[chosen], weighed.capacity[chosen], price, expected,
            _streaks_in(costs, record)[weighed.good[chosen], weighed.area[chosen]], skipped[weighed.good[chosen], weighed.area[chosen]],
            first, count, recipe, cost, entry_plan_pack.block_tuple(block), costs.tables, costs.matrices.outputs,
            entry_plan_pack.siting_state(costs), costs._site_tables, index.of_good_tile, plans, years_out, counted)
        if made < 0:
            raise RuntimeError("the margin plan table ran out of rows")
    sub = Weighed.__new__(Weighed)
    sub.good, sub.area = weighed.good[chosen], weighed.area[chosen]
    _write_streaks(costs, record, sub, years_out, counted)
    return plans


def trial_plan_table(costs, block, weighed: Weighed, skipped: np.ndarray):
    """The `EntryPlans` of the trial rule: the markets with bids, no maker in their area and no plan from an earlier rule."""
    index = costs.arrays.area_index
    chosen = np.flatnonzero((weighed.capacity <= 0.0) & ~skipped[weighed.good, weighed.area])
    good, anchor, place, price = weighed.good[chosen], weighed.anchor[chosen], weighed.place[chosen], weighed.price[chosen]
    booked, booked_cost, booked_first, booked_count = ranked_by_cost(costs, good, anchor, np.full(len(chosen), np.nan))
    trial = np.flatnonzero(booked_count > 0)
    good, anchor, place, price = good[trial], anchor[trial], place[trial], price[trial]
    positive = ~np.isnan(price) & (price > 0.0)
    reference = np.where(positive, price, booked_cost[booked_first[trial]] * (1.0 + ENTRY_PRICE_MARGIN_SHARE)) if len(trial) else np.zeros(0)
    wanted = block.demand_at_many(place, reference, reference) if len(trial) else np.zeros(0)
    recipe, cost, first, count = ranked_by_cost(costs, good, anchor, ENTRY_SHARE_OF_UNTRADED_DEMAND * wanted)
    plans = entry_plan_table.empty(len(recipe))
    if len(trial):
        entry_plan_pack.site_tables(costs, recipe)
        made = trial_plans(good, anchor, place, price, first, count, recipe, cost, entry_plan_pack.block_tuple(block), costs.tables,
                           costs.matrices.outputs, entry_plan_pack.siting_state(costs), costs._site_tables, index.of_good_tile, plans)
        if made < 0:
            raise RuntimeError("the trial plan table ran out of rows")
    return plans
