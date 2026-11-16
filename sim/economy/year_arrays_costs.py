"""What a unit of each producer's outputs costs to make, for every producer and output at once, over the year arrays.

`OfferCosts.build(arrays, interest_rate)` runs `unit_costs` once: the rules of `unit_cost.full_cost_per_unit` and
`seller_offers.cost_figures` (inputs and plant at the remembered prices of the producer's tile, labour at the wage rule,
the capital charge at the live rate, the joint cost shared by value among the outputs) for each row of the producer
columns and each output slot of its recipe. A price or wage the memory does not hold makes the cost infinite. The arrays
are those of the year start refreshed by `YearArrays.sync`; nothing here writes the records."""
from dataclasses import dataclass, replace

import math

import numpy as np

from sim.jit import njit

from .producers import COST_SPREAD_WITHIN_PRODUCER
from .setup import labour_area
from .year_arrays_memory import MemoryArrays
from .year_arrays_recipes import NO_SLOT

KERNEL = {"error_model": "numpy"}


@njit(**KERNEL)
def price_in(grid, area_of, good, tile):
    """The (good, area) cell of the area `good` has on `tile`; NaN where the good has no market there."""
    column = area_of[good, tile]
    return np.nan if column < 0 else grid[good, column]


@njit(**KERNEL)
def recovery_factor(rate, life_years):
    """capital_market.capital_recovery_factor for a positive life."""
    paid_off = -np.expm1(-life_years * np.log1p(rate)) if rate > 0.0 else 0.0
    return rate / paid_off if paid_off > 0.0 else 1.0 / life_years


@njit(**KERNEL)
def bill_goods(quantities, price, area_of, tile):
    """The cost of a row of quantities at the tile's prices (unit_cost._bill): infinite when a used good has no price."""
    total = 0.0
    for good in range(len(quantities)):
        if quantities[good] > 0.0:
            found = price_in(price, area_of, good, tile)
            if np.isnan(found):
                return np.inf
            total += quantities[good] * found
    return total


@njit(**KERNEL)
def bill_hours(hours, wage, tile):
    total = 0.0
    for trade in range(len(hours)):
        if hours[trade] > 0.0:
            found = wage[trade, tile]
            if np.isnan(found):
                return np.inf
            total += hours[trade] * found
    return total


@njit(**KERNEL)
def share_working(revenue, variable, spread):
    """producers.share_working: the share of a producer's workplaces whose own cost the revenue covers."""
    if variable <= 0.0:
        return 1.0
    if revenue <= 0.0:
        return 0.0
    ratio = revenue / variable
    if not ratio > 0.0:
        return 0.0
    score = (np.log(ratio) + spread * spread / 2.0) / spread
    return 0.5 * (1.0 + math.erf(score / math.sqrt(2.0)))


@njit(**KERNEL)
def unit_costs(recipe_row, tile_row, yield_factor, rent, held_expected, slot_goods, inputs_bill, planned_inputs_bill, outputs, plant_goods,
               labour_hours, plant_labour_hours, plant_life, price, offered, wage, area_of, rate, spread, revenue_outputs):
    """(cost, input share of the run's variable cost, expected price) by producer row and recipe slot, for the slots that
    are outputs of the producer's recipe (NaN elsewhere); and by producer row the share of its plant a run pays at the prices it
    plans with (producers.share_that_pays), the revenue of which is the outputs `revenue_outputs` as they fetch after the state's
    harvest share. The expected price is the producer's own, else the price on offer in its
    market, NaN where neither. `inputs_bill` and `planned_inputs_bill` (by producer row) are `grid_wear.input_bills`: the inputs at the
    tile's prices and at the prices a plan costs them at, a tool with no price covered by its fallback."""
    producers, slots = held_expected.shape
    pays = np.zeros(producers)
    cost = np.full((producers, slots), np.nan)
    share = np.zeros((producers, slots))
    expected = np.full((producers, slots), np.nan)
    for row in range(producers):
        recipe, tile = recipe_row[row], tile_row[row]
        input_bill = inputs_bill[row]
        plant_value = bill_goods(plant_goods[recipe], price, area_of, tile) + bill_hours(plant_labour_hours[recipe], wage, tile)
        variable = input_bill + bill_hours(labour_hours[recipe], wage, tile) + rent[row]
        if plant_value == 0.0:
            charge = 0.0
        elif plant_life[recipe] <= 0.0:
            charge = plant_value
        else:
            charge = plant_value * recovery_factor(rate, plant_life[recipe])
        run_cost = variable + charge
        input_share = input_bill / variable if np.isfinite(variable) and variable > 0.0 else 0.0
        planned = planned_inputs_bill[row] + bill_hours(labour_hours[recipe], wage, tile) + rent[row]
        revenue = 0.0
        kept_revenue = 0.0
        total_output = 0.0
        for slot in range(slots):
            good = slot_goods[recipe, slot]
            if good < 0:
                break
            total_output += outputs[recipe, good]
            if outputs[recipe, good] > 0.0:
                held = held_expected[row, slot]
                found = held if not np.isnan(held) else price_in(offered, area_of, good, tile)
                expected[row, slot] = found
                if not np.isnan(found):
                    revenue += outputs[recipe, good] * found
                    kept_revenue += revenue_outputs[recipe, good] * found
        for slot in range(slots):
            good = slot_goods[recipe, slot]
            if good < 0:
                break
            if outputs[recipe, good] <= 0.0:
                continue
            share[row, slot] = input_share
            made = outputs[recipe, good] * yield_factor[row]
            if made <= 0.0 or not np.isfinite(run_cost):
                cost[row, slot] = np.inf
                continue
            own_price = expected[row, slot]
            own_value = outputs[recipe, good] * own_price if not np.isnan(own_price) else 0.0
            if revenue > 0.0 and own_value > 0.0:
                part = own_value / revenue
            else:
                part = outputs[recipe, good] / total_output
            cost[row, slot] = run_cost * part / made
        pays[row] = share_working(kept_revenue * yield_factor[row], planned, spread) if np.isfinite(planned) else 0.0
    return cost, share, expected, pays


def slot_table(matrices) -> np.ndarray:
    """Recipe row by good column: the good's slot in the recipe's slot list, NO_SLOT where the recipe does not touch it."""
    slot_of = np.full((len(matrices.recipes.ids), len(matrices.goods.ids)), NO_SLOT, dtype=np.int64)
    for recipe, goods in enumerate(matrices.slot_goods):
        for slot, good in enumerate(goods):
            if good != NO_SLOT:
                slot_of[recipe, good] = slot
    return slot_of


@dataclass(frozen=True)
class OfferCosts:
    cost: np.ndarray           # producer row by recipe slot
    input_share: np.ndarray
    expected: np.ndarray
    slot_of: np.ndarray        # recipe row by good column
    pays: np.ndarray           # producer row: the share of its plant a run pays (producers.share_that_pays)

    @classmethod
    def build(cls, arrays, interest_rate: float) -> "OfferCosts":
        matrices, producers, memory = arrays.matrices, arrays.producers, arrays.memory
        from .grid_wear import input_bills       # grid_wear reads this module's kernels
        slot_of = slot_table(matrices)
        at_price, planned = input_bills(producers.recipe_row, producers.tile_row, producers.expected_prices, matrices.slot_goods,
                                        matrices.inputs, arrays.tools, matrices.labour_hours, memory.wage, memory.price,
                                        arrays.area_index.of_good_tile)
        cost, share, expected, pays = unit_costs(
            producers.recipe_row, producers.tile_row, producers.yield_factor, producers.land_rent_per_run,
            producers.expected_prices, matrices.slot_goods, at_price, planned, matrices.outputs, matrices.plant_goods,
            matrices.labour_hours, matrices.plant_labour_hours, matrices.plant_life_years, memory.price, memory.offered,
            memory.wage, arrays.area_index.of_good_tile, float(interest_rate), COST_SPREAD_WITHIN_PRODUCER,
            arrays.revenue_outputs)
        return cls(cost, share, expected, slot_of, pays)


def refreshed(arrays, setup, record, view):
    """`arrays` in step with the records now, for a phase that reads only the producers and the market memory: producers
    replaced, entered or left re-read, the memory read again with each wage worked out once per trade and labour area
    (the wage rule reads the area, not the tile). A tile no array knows rebuilds the lot (`YearArrays.sync`)."""
    try:
        producers = arrays.producers.refresh(record.producers)
    except KeyError:
        return arrays.sync(setup, record, view)
    if arrays.memory.is_current(record.memory):
        return replace(arrays, producers=producers)
    from .year_arrays import wage_grid
    memory = MemoryArrays.build(record.memory, arrays.matrices.goods, arrays.matrices.trades, arrays.tiles,
                                arrays.area_index, setup.currency_id, None,
                                wage_grid(setup, view, arrays.matrices.trades, arrays.tiles))
    return replace(arrays, producers=producers, memory=memory)
