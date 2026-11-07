"""Every producer's yearly plan in one kernel, over the year arrays (`producers.plan`, rule for rule).

`plan_rows` takes the producer columns of the rows to plan, the recipe matrices, the memory arrays and, by row and recipe
slot, the stocks held, and returns the runs, the runs wanted, the wage line and, by slot, the labour bids (hours, ceiling)
and the input bids (quantity, price, budget, ceiling). A recipe with tool fallbacks, tool wear or a practised crew is not
planned here (`plan_year.py` sends it through `producers.plan`). A price or wage the memory lacks is NaN."""
import math

import numpy as np

from sim.jit import njit

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
def stock_runs(sales, yield_factor, variable, made, stock, price, cover, clearing_years):
    """producers.runs_for_stock over the recipe's slots: `made` the units a run makes of each slot's good (0 elsewhere),
    `stock` held, `price` the expected output price (NaN where none)."""
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
        total = 0.0
        paying = -1
        best = -np.inf
        for slot in range(slots):
            if made[slot] > 0.0 and not np.isnan(price[slot]):
                value = made[slot] * price[slot]
                total += value
                if value > best:
                    best, paying = value, slot
        if paying < 0:
            for slot in range(slots):
                if made[slot] > 0.0:
                    paying = slot
                    break
        for slot in range(slots):
            if piling[slot] and slot != paying:
                value = made[slot] * price[slot] if not np.isnan(price[slot]) else np.nan
                if np.isnan(value) or not value >= total - value:
                    counted[slot] = False
        sells = 0.0
        for slot in range(slots):
            if made[slot] > 0.0 and not piling[slot] and not np.isnan(price[slot]):
                sells += made[slot] * price[slot]
        sells *= yield_factor
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
              cash, stock, slot_goods, slot_trades, inputs, outputs, labour_hours, price, offered, cleared, wage, area_of,
              spread, change_share, clearing_years, cover):
    """(runs, wanted, wage line, labour hours, labour ceilings, bid quantity, bid price, bid budget, bid ceiling), the last
    four by row and good slot and the labour pair by row and trade slot; a bid slot holds quantity zero where there is no bid."""
    count, good_slots = held_expected.shape
    trade_slots = slot_trades.shape[1]
    runs_out, wanted_out, line_out = np.zeros(count), np.zeros(count), np.zeros(count)
    hours_out, ceiling_out = np.zeros((count, trade_slots)), np.zeros((count, trade_slots))
    quantity_out, price_out = np.zeros((count, good_slots)), np.zeros((count, good_slots))
    budget_out, worth_out = np.zeros((count, good_slots)), np.zeros((count, good_slots))
    market = np.empty(good_slots)
    expected_out = np.empty(good_slots)
    made = np.empty(good_slots)
    for row in range(count):
        if idle[row] > 0:
            continue
        recipe, tile = recipe_row[row], tile_row[row]
        market[:], expected_out[:], made[:] = np.nan, np.nan, 0.0
        revenue = 0.0
        input_cost = 0.0
        priced = True
        for slot in range(good_slots):
            good = slot_goods[recipe, slot]
            market[slot], expected_out[slot], made[slot] = np.nan, np.nan, 0.0
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
                held = held_expected[row, slot]
                found = held if not np.isnan(held) else price_in(offered, area_of, good, tile)
                expected_out[slot] = found
                if not np.isnan(found):
                    revenue += outputs[recipe, good] * found
            if inputs[recipe, good] > 0.0:
                if np.isnan(live):
                    priced = False
                else:
                    plan_price = held_expected[row, slot] if not np.isnan(held_expected[row, slot]) else live
                    input_cost += inputs[recipe, good] * plan_price
        revenue *= yield_factor[row]
        labour_cost = 0.0
        total_hours = 0.0
        for slot in range(trade_slots):
            trade = slot_trades[recipe, slot]
            if trade < 0:
                break
            hours = labour_hours[recipe, trade]
            if hours > 0.0:
                total_hours += hours
                if np.isnan(wage[trade, tile]):
                    priced = False
                else:
                    labour_cost += hours * wage[trade, tile]
        variable = input_cost + labour_cost + rent[row] if priced else np.inf
        if capacity[row] <= 0.0 or revenue <= 0.0 or not np.isfinite(variable):
            continue
        market_cost = 0.0
        held_value = 0.0
        for slot in range(good_slots):
            good = slot_goods[recipe, slot]
            if good < 0:
                break
            if inputs[recipe, good] > 0.0:
                market_cost += inputs[recipe, good] * market[slot]
                held_value += min(stock[row, slot], inputs[recipe, good] * capacity[row]) * market[slot]
        paid_now = market_cost + labour_cost
        affordable = (max(cash[row], 0.0) + held_value) / paid_now if paid_now > 0.0 else capacity[row]
        chosen = min(capacity[row] * share_working(revenue, variable, spread),
                     stock_runs(sales[row], yield_factor[row], variable, made, stock[row], expected_out, cover, clearing_years))
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
            bill = labour_cost
            for slot in range(trade_slots):
                trade = slot_trades[recipe, slot]
                if trade < 0:
                    break
                hours = labour_hours[recipe, trade]
                if hours > 0.0:
                    hours_out[row, slot] = runs * hours
                    ceiling_out[row, slot] = room / total_hours if bill <= 0.0 else wage[trade, tile] * room / bill
        live_variable = market_cost + labour_cost + rent[row]
        margin = revenue / ratio - live_variable
        spendable = max(cash[row], 0.0) - runs * labour_cost
        total_cost = 0.0
        for slot in range(good_slots):
            good = slot_goods[recipe, slot]
            if good < 0:
                break
            if inputs[recipe, good] > 0.0:
                short = runs * inputs[recipe, good] - stock[row, slot]
                if short > 0.0:
                    quantity_out[row, slot] = short
                    total_cost += short * market[slot]
        for slot in range(good_slots):
            if quantity_out[row, slot] > 0.0:
                bid_price = market[slot]
                share = quantity_out[row, slot] * bid_price / total_cost if total_cost > 0.0 else 0.0
                worth = bid_price * (1.0 + max(0.0, margin) / live_variable) if live_variable > 0.0 else bid_price
                price_out[row, slot] = bid_price
                budget_out[row, slot] = max(0.0, spendable) * share
                worth_out[row, slot] = worth
    return runs_out, wanted_out, line_out, hours_out, ceiling_out, quantity_out, price_out, budget_out, worth_out
