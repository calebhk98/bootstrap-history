"""The unit-cost and price rules the year's close reads, as numba scalar functions over a producer's slots.

A producer's goods are the slots of its recipe (`year_arrays_recipes`): `quantity[w]` and `price[w]` run over them, and a
missing price is NaN. Each function is the rule of the same name in unit_cost.py, producers.py, ask_adjust.py,
inventory.py and firm_finance.py; a bill with a missing price is infinite, as there. `close_kernel.py` calls these."""
import math

import numpy as np

from sim.jit import njit


@njit
def capital_recovery_factor(rate, life_years):
    paid_off = -math.expm1(-life_years * math.log1p(rate)) if rate > 0.0 else 0.0
    return rate / paid_off if paid_off > 0.0 else 1.0 / life_years


@njit
def bill(quantity, price, count):
    """unit_cost._bill: the sum of quantity times price over the slots with a positive quantity; infinite when one lacks a price."""
    total = 0.0
    for slot in range(count):
        if quantity[slot] <= 0.0:
            continue
        if np.isnan(price[slot]):
            return np.inf
        total += quantity[slot] * price[slot]
    return total


@njit
def revenue_per_run(quantity, price, count):
    """unit_cost.revenue_per_run: outputs at their price, an output with none left out."""
    total = 0.0
    for slot in range(count):
        if not np.isnan(price[slot]):
            total += quantity[slot] * price[slot]
    return total


@njit
def capital_charge(plant_value, plant_life_years, rate):
    if plant_value == 0.0:
        return 0.0
    if plant_life_years <= 0.0:
        return plant_value
    return plant_value * capital_recovery_factor(rate, plant_life_years)


@njit
def share_working(revenue, variable_cost, spread):
    """producers.share_working: the share of workplaces whose cost the revenue covers (costs log-normal with spread `spread`)."""
    if variable_cost <= 0.0:
        return 1.0
    if revenue <= 0.0:
        return 0.0
    ratio = revenue / variable_cost
    if not ratio > 0.0:
        score = -np.inf
    else:
        score = (math.log(ratio) + spread * spread / 2.0) / spread
    return 0.5 * (1.0 + math.erf(score / math.sqrt(2.0)))


@njit
def band_edge(break_even, input_share, ceiling_multiple):
    share = min(1.0, max(0.0, input_share))
    return break_even * (share + ceiling_multiple * (1.0 - share))


@njit
def stock_gap(stock, target):
    if target <= 0.0:
        return -1.0 if stock > 0.0 else 0.0
    return max(-1.0, min(1.0, (target - stock) / target))


@njit
def adjusted_within_band(expected, break_even, stock, target, ceiling_multiple, input_share, step):
    """ask_adjust.adjusted_within_band; `break_even` NaN is None."""
    if np.isnan(break_even) or not math.isfinite(break_even) or break_even <= 0.0:
        return expected
    moved = expected * (1.0 + step * stock_gap(stock, target))
    if moved >= expected:
        return max(expected, min(moved, band_edge(break_even, input_share, ceiling_multiple)))
    return min(expected, max(moved, break_even))


@njit
def held_to_band(expected, previous, unit_cost, input_share, ceiling_multiple):
    """planning_price.held_to_band; `previous` NaN is None."""
    if np.isnan(unit_cost) or not unit_cost > 0.0:
        return expected
    ceiling = band_edge(unit_cost, input_share, ceiling_multiple)
    if not np.isnan(previous):
        ceiling = max(ceiling, previous)
    return min(expected, ceiling)


@njit
def queued_holding_value(reservation, stock, yearly_sales, rate, spoilage):
    """inventory.queued_holding_value."""
    if yearly_sales <= 0.0 or reservation <= 0.0:
        return 0.0
    surviving = 1.0 - min(1.0, max(0.0, spoilage))
    if surviving <= 0.0:
        return 0.0
    years_waited = max(0.0, stock / yearly_sales - 1.0)
    carried = surviving / (1.0 + max(rate, -0.99))
    return reservation * carried ** years_waited


@njit
def demand_seen(sold, left, own_capacity, market_capacity, market_unmet, sold_out_share):
    """expected_sales.demand_seen."""
    if market_unmet <= 0.0 or own_capacity <= 0.0 or market_capacity <= 0.0 or left > sold_out_share * sold:
        return sold
    return sold + min(1.0, own_capacity / market_capacity) * market_unmet


@njit
def earnable_rate(gain, outlay):
    """credit.earnable_rate."""
    if not (math.isfinite(gain) and math.isfinite(outlay)) or gain <= 0.0 or outlay <= 0.0:
        return 0.0
    return gain / outlay


@njit
def within_a_years_change(last_runs, staffed, capacity, runs, change_share):
    """producers.within_a_years_change; `staffed` NaN is None."""
    if last_runs < 0.0:
        return runs
    step = change_share * capacity
    anchor = last_runs if np.isnan(staffed) else max(last_runs, min(staffed, capacity))
    return max(anchor - step, min(anchor + step, runs))


@njit
def flag_at(grid, area_of, good, tile):
    column = area_of[good, tile]
    return column >= 0 and grid[good, column]


@njit
def price_at(grid, area_of, good, tile):
    """The (good, area) cell of the area `good` has on `tile`; NaN where it has no market."""
    column = area_of[good, tile]
    return np.nan if column < 0 else grid[good, column]
