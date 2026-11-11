"""Every producer's yearly plan in one kernel, over the year arrays (`producers.plan`, rule for rule).

`plan_rows` takes the producer columns of the rows to plan, the recipe matrices and tool tables, the memory arrays and, by row and bid
place, the stocks held, and returns the runs, the runs wanted, the wage line, the labour bids (hours, ceiling) by trade slot and the
input bids (good, quantity, price, budget, ceiling) in the order the plan makes them (plan_bids.py). A crew whose practice stretches the
recipe's hours (`hours_scale`) and a recipe with tool wear and fallbacks are planned here as `producers.plan` plans them. A price or
wage the memory lacks is NaN."""
import math

import numpy as np

from sim.jit import njit

from .exact_sum import exact_sum
from .plan_bids import place_bids
from .plan_tools import run_hours
from .plan_sums import held_value_of, hours_bill, input_bill, revenue_per_run
from .year_arrays_costs import KERNEL, price_in, share_working

_ROOT_TWO = math.sqrt(2.0)


@njit(**KERNEL)
def normal_below(score):
    return 0.5 * (1.0 + math.erf(score / _ROOT_TWO))


@njit(**KERNEL)
def working_cost_ratio(revenue, variable, spread):
    """producers.working_cost_ratio."""
    if variable <= 0.0 or revenue <= 0.0:
        return 1.0
    ratio = revenue / variable
    score = -np.inf if not ratio > 0.0 else (np.log(ratio) + spread * spread / 2.0) / spread
    working = normal_below(score)
    if working <= 0.0:
        return 1.0
    return normal_below(score - spread) / working


@njit(**KERNEL)
def stock_runs(sales, yield_factor, variable, made, made_value, stock, price, cover, clearing_years):
    """producers.runs_for_stock over the recipe's slots: `made` the units a run makes of each slot's good (0 elsewhere), `made_value` the same as they fetch after the state's harvest share,
    `stock` held, `price` the expected output price (NaN where none); the sums are `math.fsum`."""
    if sales <= 0.0:
        return np.inf
    target = max(0.0, sales) * max(0.0, cover) / 12.0
    slots = len(made)
    gap = np.full(slots, np.nan)
    any_gap = False
    for slot in range(slots):
        if made[slot] * yield_factor > 0.0:
            gap[slot] = target - stock[slot] / (made[slot] * yield_factor)
            any_gap = True
    if not any_gap:
        return sales
    counted = ~np.isnan(gap)
    piling = counted & (gap < 0.0)
    if piling.any():
        paying = -1
        best = -np.inf
        terms = np.empty(slots)
        used = 0
        for slot in range(slots):
            if made[slot] > 0.0 and not np.isnan(price[slot]):
                value = made_value[slot] * price[slot]
                terms[used] = value
                used += 1
                if value > best:
                    best, paying = value, slot
        total = exact_sum(terms, used)
        if paying < 0:
            for slot in range(slots):
                if made[slot] > 0.0:
                    paying = slot
                    break
        for slot in range(slots):
            if piling[slot] and slot != paying:
                value = made_value[slot] * price[slot] if not np.isnan(price[slot]) else np.nan
                if np.isnan(value) or not value >= total - value:
                    counted[slot] = False
        used = 0
        for slot in range(slots):
            if made[slot] > 0.0 and not piling[slot] and not np.isnan(price[slot]):
                terms[used] = made_value[slot] * price[slot]
                used += 1
        sells = exact_sum(terms, used) * yield_factor
        if sells > 0.0 and sells >= variable:
            for slot in range(slots):
                if piling[slot]:
                    counted[slot] = False
    lowest = np.inf
    for slot in range(slots):
        if counted[slot] and gap[slot] < lowest:
            lowest = gap[slot]
    return max(0.0, sales + lowest / clearing_years)


@njit(**KERNEL)
def plan_rows(recipe_row, tile_row, capacity, yield_factor, rent, land_cap, sales, last_runs, staffed, idle, held_expected,
              cash, stock, hours_scale, tools, slot_goods, slot_trades, inputs, outputs, revenue_outputs, labour_hours, price, offered, cleared, wage,
              area_of, spread, change_share, clearing_years, cover):
    """(runs, wanted, wage line, labour hours, labour ceilings, bid good, bid quantity, bid price, bid budget, bid ceiling): the labour pair
    by row and trade slot (hours NaN where the trade is not bid for), the bids by row and need, in the order the plan makes them (the
    good is -1 where the row has no such bid).
    The sums are added as `producers.plan` adds them (plan_sums.py)."""
    count, good_slots = held_expected.shape
    trade_slots = slot_trades.shape[1]
    bid_width = tools.bid_goods.shape[1]
    runs_out, wanted_out, line_out = np.zeros(count), np.zeros(count), np.zeros(count)
    hours_out, ceiling_out = np.full((count, trade_slots), np.nan), np.zeros((count, trade_slots))
    good_out = np.full((count, bid_width), -1, dtype=np.int64)
    quantity_out, price_out = np.zeros((count, bid_width)), np.zeros((count, bid_width))
    budget_out, worth_out = np.zeros((count, bid_width)), np.zeros((count, bid_width))
    market, plan_price = np.empty(bid_width), np.empty(good_slots)
    expected_out = np.empty(good_slots)
    made = np.empty(good_slots)
    made_value = np.empty(good_slots)
    wanted_at, placed, order_place = np.zeros(bid_width), np.empty(bid_width, dtype=np.int64), np.empty(bid_width, dtype=np.int64)
    terms = np.zeros(max(bid_width, good_slots) + tools.step_trade.shape[2] + 1)
    hour_terms = np.zeros(2 * trade_slots)
    for row in range(count):
        if idle[row] > 0:
            continue
        recipe, tile = recipe_row[row], tile_row[row]
        market[:], plan_price[:], expected_out[:], made[:], made_value[:] = np.nan, np.nan, np.nan, 0.0, 0.0
        priced = True
        for slot in range(good_slots):
            good = slot_goods[recipe, slot]
            if good < 0:
                break
            live = price_in(price, area_of, good, tile)
            if inputs[recipe, good] > 0.0 and not np.isnan(live):
                paid = price_in(cleared, area_of, good, tile)
                if not np.isnan(paid) and paid > live:
                    live = paid
            market[slot] = live
            if outputs[recipe, good] > 0.0:
                made[slot] = outputs[recipe, good]
                made_value[slot] = revenue_outputs[recipe, good]
                held = held_expected[row, slot]
                expected_out[slot] = held if not np.isnan(held) else price_in(offered, area_of, good, tile)
            if inputs[recipe, good] > 0.0:
                if np.isnan(live):
                    priced = False
                else:
                    plan_price[slot] = held_expected[row, slot] if not np.isnan(held_expected[row, slot]) else live
        revenue = revenue_per_run(recipe, slot_goods, revenue_outputs, expected_out, terms) * yield_factor[row]
        input_cost = input_bill(recipe, slot_goods, inputs, tools.input_order, plan_price)
        labour_cost, total_hours, claimed_bill, hours_priced = hours_bill(
            row, recipe, tile, slot_trades, tools.hours_order, labour_hours, hours_scale, wage, hour_terms)
        variable = input_cost + labour_cost + rent[row] if priced and hours_priced else np.inf
        if capacity[row] <= 0.0 or revenue <= 0.0 or not np.isfinite(variable):
            continue
        market_cost = input_bill(recipe, slot_goods, inputs, tools.input_order, market)
        held_value = held_value_of(row, recipe, slot_goods, inputs, tools.input_order, capacity[row], stock, market, terms)
        paid_now = market_cost + labour_cost
        affordable = (max(cash[row], 0.0) + held_value) / paid_now if paid_now > 0.0 else capacity[row]
        chosen = min(capacity[row] * share_working(revenue, variable, spread),
                     stock_runs(sales[row], yield_factor[row], variable, made, made_value, stock[row], expected_out, cover, clearing_years))
        if last_runs[row] >= 0.0:
            step = change_share * capacity[row]
            anchor = last_runs[row]
            if not np.isnan(staffed[row]):
                anchor = max(anchor, min(staffed[row], capacity[row]))
            chosen = max(anchor - step, min(anchor + step, chosen))
        runs = max(0.0, min(chosen, affordable))
        wanted_out[row] = runs
        if not np.isnan(land_cap[row]):
            runs = min(runs, land_cap[row])
        ratio = working_cost_ratio(revenue, variable, spread)
        if runs <= 0.0 or ratio <= 0.0:
            continue
        runs_out[row] = runs
        line_out[row] = runs * labour_cost
        room = max(0.0, revenue / ratio - (input_cost + rent[row]))
        if total_hours > 0.0:
            for slot in range(trade_slots):
                trade = slot_trades[recipe, slot]
                if trade < 0:
                    break
                if tools.listed_hours[recipe, trade]:
                    hours_out[row, slot] = runs * run_hours(labour_hours, hours_scale, recipe, row, trade)
                    ceiling_out[row, slot] = room / total_hours if claimed_bill <= 0.0 else wage[trade, tile] * room / claimed_bill
        live_variable = market_cost + labour_cost + rent[row]
        for place in range(good_slots, bid_width):          # the fallback goods that are not inputs
            good = tools.bid_goods[recipe, place]
            market[place] = price_in(price, area_of, good, tile) if good >= 0 else np.nan
        place_bids(row, recipe, tile, runs, max(cash[row], 0.0) - runs * labour_cost, revenue / ratio - live_variable, live_variable,
                   stock, market, slot_goods, inputs, tools, labour_hours, hours_scale, wage, good_out, quantity_out, price_out, budget_out,
                   worth_out, wanted_at, placed, order_place, terms)
    return runs_out, wanted_out, line_out, hours_out, ceiling_out, good_out, quantity_out, price_out, budget_out, worth_out
