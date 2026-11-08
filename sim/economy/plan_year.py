"""The year's plans for every producer: one kernel call over the year arrays (`plan_kernel.plan_rows`), then `Plan` records.

`plans_of(setup, record, view, arrays, money)` is `{producer_id: producers.plan(...)}` for every producer in sorted id order.
A producer whose recipe has tool fallbacks or tool wear, a zero quantity or hour entry, or whose crew's practice stretches
the recipe's hours is planned by `producers.plan` itself."""
from typing import Dict

import numpy as np

from . import practice, producers
from .inventory import DEFAULT_MONTHS_OF_COVER
from .plan_kernel import plan_rows
from .goods_order_objects import make_bid
from .types import LabourBid
from .year_arrays_recipes import RecipeMatrices

_simple: Dict[int, tuple] = {}      # id of the recipes mapping -> (mapping, recipe id -> whether the kernel plans it)


def simple_recipes(recipes) -> Dict[str, bool]:
    """Which recipes the kernel plans: no tool fallbacks or wear, every input, output and hour entry positive."""
    kept = _simple.get(id(recipes))
    if kept is None or kept[0] is not recipes or kept[2] != len(recipes):
        flags = {recipe_id: not recipe.tool_fallbacks and not recipe.tool_wear
                 and all(quantity > 0.0 for quantity in recipe.inputs.values())
                 and all(quantity > 0.0 for quantity in recipe.outputs.values())
                 and all(quantity > 0.0 for quantity in recipe.labour_hours.values())
                 for recipe_id, recipe in recipes.items()}
        kept = _simple[id(recipes)] = (recipes, flags, len(recipes))
    return kept[1]


def slot_names(matrices: RecipeMatrices):
    """By recipe row: ((slot, good id) of the inputs and outputs, (slot, good id) of the inputs, (slot, trade id) of the trades)."""
    goods, trades = matrices.goods.ids, matrices.trades.ids
    table = []
    for recipe in range(len(matrices.recipes.ids)):
        slots = matrices.slot_goods[recipe]
        held = tuple((slot, goods[good]) for slot, good in enumerate(slots)
                     if good >= 0 and (matrices.slot_is_input[recipe, slot] or matrices.slot_is_output[recipe, slot]))
        bought = tuple((slot, goods[good]) for slot, good in enumerate(slots) if good >= 0 and matrices.slot_is_input[recipe, slot])
        hired = tuple((slot, trades[trade]) for slot, trade in enumerate(matrices.slot_trades[recipe])
                      if trade >= 0 and matrices.labour_hours[recipe, trade] > 0.0)
        table.append((held, bought, hired))
    return table


def stocks_by_slot(record, columns, names, rows, slots: int) -> np.ndarray:
    """Stock held by row and good slot, for the slots that are an input or an output of the row's recipe."""
    stock = np.zeros((len(rows), slots))
    held = record.book.stock
    recipe_rows = columns.recipe_row[np.array(rows, dtype=np.int64)].tolist()
    records = columns.records
    for position, row in enumerate(rows):
        producer = records[row]
        agent, tile = producer.agent_id, producer.tile
        line = stock[position]
        for slot, good in names[recipe_rows[position]][0]:
            line[slot] = held(agent, good, tile)
    return stock


def plans_of(setup, record, view, arrays, money) -> Dict[str, producers.Plan]:
    columns = arrays.producers.refresh(record.producers)
    matrices, memory = arrays.matrices, arrays.memory
    flags = simple_recipes(setup.recipes)
    recipes = setup.recipes
    plain = [row for row, producer in enumerate(columns.records)
             if flags[producer.recipe_id] and (not producer.crew_runs or practice.recipe_for(
                 recipes[producer.recipe_id], producer.crew_runs) is recipes[producer.recipe_id])]
    rows = np.array(plain, dtype=np.int64)
    names = slot_names(matrices)
    ids = columns.ids
    cash = np.array([record.book.balance(ids[row], money) for row in plain])
    stock = stocks_by_slot(record, columns, names, plain, matrices.good_slots)
    (runs, wanted, line, hours, ceilings, quantity, bid_price, budget, worth) = plan_rows(
        columns.recipe_row[rows], columns.tile_row[rows], columns.capacity_runs[rows], columns.yield_factor[rows],
        columns.land_rent_per_run[rows], columns.land_run_cap[rows], columns.expected_sales[rows], columns.last_runs[rows],
        columns.staffed_runs[rows], columns.idle_years[rows], columns.expected_prices[rows], cash, stock, matrices.slot_goods,
        matrices.slot_trades, matrices.inputs, matrices.outputs, matrices.labour_hours, memory.price, memory.offered,
        memory.cleared, memory.wage, arrays.area_index.of_good_tile, producers.COST_SPREAD_WITHIN_PRODUCER,
        producers.OUTPUT_CHANGE_SHARE_PER_YEAR, producers.STOCK_CLEARING_YEARS, DEFAULT_MONTHS_OF_COVER)
    recipe_of = columns.recipe_row[rows].tolist()
    runs_list, wanted_list, line_list = runs.tolist(), wanted.tolist(), line.tolist()
    area_of = view.area_of
    plans = {}
    hours_rows, ceiling_rows = hours.tolist(), ceilings.tolist()
    quantity_rows, price_rows, budget_rows, worth_rows = quantity.tolist(), bid_price.tolist(), budget.tolist(), worth.tolist()
    for position, row in enumerate(plain):
        producer = columns.records[row]
        agent = producer.agent_id
        if runs_list[position] <= 0.0:
            plans[agent] = producers.Plan(0.0, wanted_runs=wanted_list[position])
            continue
        _held, bought, hired = names[recipe_of[position]]
        tile = producer.tile
        hours_row, ceiling_row = hours_rows[position], ceiling_rows[position]
        quantity_row = quantity_rows[position]
        labour_bids = tuple(LabourBid(agent, trade, area_of(trade, tile), hours_row[slot], ceiling_row[slot]) for slot, trade in hired)
        price_row, budget_row, worth_row = price_rows[position], budget_rows[position], worth_rows[position]
        bids = tuple(make_bid(agent, good, area_of(good, tile), tile, quantity_row[slot], 0.0, price_row[slot], 0.0, budget_row[slot], 0,
                              worth_row[slot]) for slot, good in bought if quantity_row[slot] > 0.0)
        plans[agent] = producers.Plan(runs_list[position], labour_bids, bids, wanted_list[position], line_list[position])
    for producer_id in ids:
        if producer_id not in plans:
            producer = record.producers[producer_id]
            plans[producer_id] = producers.plan(producer, recipes[producer.recipe_id], view, record.book.balance(producer_id, money))
    return {producer_id: plans[producer_id] for producer_id in ids}
