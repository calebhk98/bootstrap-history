"""What each good costs to make by its cheapest recipe, every good in input-depth order in one kernel call (`notional` reads it).

The rules are `unit_cost.full_cost_per_unit` with no maker or site named (yield one, no rent) taken over `recipes.recipes_making`, and the
estimate loop of `notional._estimated_prices`. A recipe's goods and hours are read in the order its dictionaries hold them and added left to
right, as `unit_cost._bill` adds them, and the sums that were `math.fsum` are exact (`opening_demand_kernel`), so every figure equals the
Python's to the last bit.

`RecipeTables` holds the setup's recipes as runs (compressed rows): for each recipe its inputs, labour hours, plant goods, plant hours and
outputs, and for each good the recipes that make it. A good or trade a price is missing for is NaN in the price vectors, and a run that needs
it costs infinity (`unit_cost._bill`)."""
import math
from typing import Dict, List, Mapping

import numpy as np

from sim.jit import njit

from .opening_demand_kernel import PARTIALS, _add, _total
from .recipes import input_depth_order, recipes_making

COSTS_ONLY = 0        # `making_costs`: every good costed at the prices given
ESTIMATES = 1         # `_estimated_prices`: goods untraded lately costed, and (`thin`) thin markets blended, each estimate seen by the goods after it


class RecipeTables:
    """A mapping of recipes as runs of (item number, quantity), in the order each recipe's dictionaries hold them."""

    def __init__(self, recipes: Mapping[str, object]) -> None:
        order = input_depth_order(recipes)
        goods = set(order)
        trades = set()
        for recipe in recipes.values():
            goods.update(recipe.inputs, recipe.outputs, recipe.plant_goods)
            trades.update(recipe.labour_hours, recipe.plant_labour_hours)
        self.goods: List[str] = sorted(goods)
        self.trades: List[str] = sorted(trades)
        good_number = {name: number for number, name in enumerate(self.goods)}
        trade_number = {name: number for number, name in enumerate(self.trades)}
        listed = list(recipes.values())
        self.inputs = _runs(listed, "inputs", good_number)
        self.labour = _runs(listed, "labour_hours", trade_number)
        self.plant_goods = _runs(listed, "plant_goods", good_number)
        self.plant_labour = _runs(listed, "plant_labour_hours", trade_number)
        self.outputs = _runs(listed, "outputs", good_number)
        self.plant_life = np.array([recipe.plant_life_years for recipe in listed], dtype=np.float64)
        self.order = np.array([good_number[name] for name in order], dtype=np.int64)
        starts, chosen = [0], []
        position_of = {id(recipe): place for place, recipe in enumerate(listed)}
        for name in self.goods:
            chosen.extend(position_of[id(recipe)] for recipe in recipes_making(recipes, name))
            starts.append(len(chosen))
        self.makers_start = np.array(starts, dtype=np.int64)
        self.makers = np.array(chosen, dtype=np.int64)


def _runs(recipes, field: str, number: Dict[str, int]) -> tuple:
    """(start of each recipe's run, item number, quantity) of the dictionary `field` of each recipe."""
    starts, items, quantities = [0], [], []
    for recipe in recipes:
        for name, quantity in getattr(recipe, field).items():
            items.append(number[name])
            quantities.append(quantity)
        starts.append(len(items))
    return np.array(starts, dtype=np.int64), np.array(items, dtype=np.int64), np.array(quantities, dtype=np.float64)


_kept: Dict[int, tuple] = {}


def tables_of(recipes: Mapping[str, object]) -> RecipeTables:
    """The `RecipeTables` of a recipes mapping, kept while it is the same mapping and the same size (a setup replaces its mapping when a
    recipe is admitted); the mapping is held, so its id is never read for another."""
    kept = _kept.get(id(recipes))
    if kept is None or kept[0] is not recipes or kept[1] != len(recipes):
        if len(_kept) >= 8:
            _kept.clear()
        kept = _kept[id(recipes)] = (recipes, len(recipes), RecipeTables(recipes))
    return kept[2]


@njit
def bill(start, items, quantities, recipe, prices):
    """`unit_cost._bill` of one recipe's run: the quantities at `prices` (by item number) added in order; infinite where a used item has none."""
    total = 0.0
    for place in range(start[recipe], start[recipe + 1]):
        if quantities[place] <= 0.0:
            continue
        found = prices[items[place]]
        if np.isnan(found):
            return np.inf
        total += quantities[place] * found
    return total


@njit
def recovery_factor(rate, life_years):
    """`capital_market.capital_recovery_factor` for a positive life."""
    paid_off = -math.expm1(-life_years * math.log1p(rate)) if rate > 0.0 else 0.0
    return rate / paid_off if paid_off > 0.0 else 1.0 / life_years


@njit
def unit_cost_of(recipe, good, inputs_start, inputs_item, inputs_quantity, labour_start, labour_item, labour_quantity, plant_start,
                 plant_item, plant_quantity, plant_hours_start, plant_hours_item, plant_hours_quantity, outputs_start, outputs_item,
                 outputs_quantity, plant_life, live, wages, rate, partials):
    """`unit_cost.full_cost_per_unit(recipe, good, live, live, wages, rate)`."""
    made = 0.0
    for place in range(outputs_start[recipe], outputs_start[recipe + 1]):
        if outputs_item[place] == good:
            made = outputs_quantity[place]
    if made <= 0.0:
        return np.inf
    variable = bill(inputs_start, inputs_item, inputs_quantity, recipe, live) + bill(
        labour_start, labour_item, labour_quantity, recipe, wages) + 0.0
    value = bill(plant_start, plant_item, plant_quantity, recipe, live) + bill(
        plant_hours_start, plant_hours_item, plant_hours_quantity, recipe, wages)
    if value == 0.0:
        charge = 0.0
    elif plant_life[recipe] <= 0.0:
        charge = value
    else:
        charge = value * recovery_factor(rate, plant_life[recipe])
    run_cost = variable + charge
    if not np.isfinite(run_cost):
        return np.inf
    count = 0
    for place in range(outputs_start[recipe], outputs_start[recipe + 1]):
        price = live[outputs_item[place]]
        if not np.isnan(price):
            count = _add(partials, count, outputs_quantity[place] * price)
    revenue = _total(partials, count)
    own_price = live[good]
    own_value = made * own_price if not np.isnan(own_price) else 0.0
    if revenue > 0.0 and own_value > 0.0:
        share = own_value / revenue
    else:
        count = 0
        for place in range(outputs_start[recipe], outputs_start[recipe + 1]):
            count = _add(partials, count, outputs_quantity[place])
        share = made / _total(partials, count)
    return run_cost * share / made


@njit
def cheapest_cost_of(good, makers_start, makers, inputs_start, inputs_item, inputs_quantity, labour_start, labour_item, labour_quantity,
                     plant_start, plant_item, plant_quantity, plant_hours_start, plant_hours_item, plant_hours_quantity, outputs_start,
                     outputs_item, outputs_quantity, plant_life, live, wages, rate, partials):
    """`notional.cheapest_cost`: the least cost over the recipes making `good`; NaN when none can be priced."""
    best = np.inf
    for place in range(makers_start[good], makers_start[good + 1]):
        cost = unit_cost_of(makers[place], good, inputs_start, inputs_item, inputs_quantity, labour_start, labour_item, labour_quantity,
                            plant_start, plant_item, plant_quantity, plant_hours_start, plant_hours_item, plant_hours_quantity,
                            outputs_start, outputs_item, outputs_quantity, plant_life, live, wages, rate, partials)
        if cost < best:
            best = cost
    return best if np.isfinite(best) and best > 0.0 else np.nan


@njit
def costed_goods(mode, order, makers_start, makers, inputs_start, inputs_item, inputs_quantity, labour_start, labour_item, labour_quantity,
                 plant_start, plant_item, plant_quantity, plant_hours_start, plant_hours_item, plant_hours_quantity, outputs_start,
                 outputs_item, outputs_quantity, plant_life, live, in_live, wages, rate, recent, thin, wanted, traded, thin_share):
    """The cost estimate of each good (NaN for none) taking the goods in `order`. With `COSTS_ONLY` each good is costed at `live` as
    given. With `ESTIMATES` a good not `recent` is costed and its cost becomes its live price for the goods after it; a recent good the
    opening wanted in bulk (`wanted` above nothing), that has a live price, and that the markets trade a sliver of (`traded` under
    `thin_share` of `wanted`), is blended toward its cost by how much of that share it trades (and `thin` is on). `live` and `in_live`
    are changed in place."""
    partials = np.zeros(PARTIALS)
    estimate = np.full(len(live), np.nan)
    for good in order:
        if mode == COSTS_ONLY:
            estimate[good] = cheapest_cost_of(good, makers_start, makers, inputs_start, inputs_item, inputs_quantity, labour_start,
                                              labour_item, labour_quantity, plant_start, plant_item, plant_quantity, plant_hours_start,
                                              plant_hours_item, plant_hours_quantity, outputs_start, outputs_item, outputs_quantity,
                                              plant_life, live, wages, rate, partials)
            continue
        if not recent[good]:
            cost = cheapest_cost_of(good, makers_start, makers, inputs_start, inputs_item, inputs_quantity, labour_start, labour_item,
                                    labour_quantity, plant_start, plant_item, plant_quantity, plant_hours_start, plant_hours_item,
                                    plant_hours_quantity, outputs_start, outputs_item, outputs_quantity, plant_life, live, wages, rate,
                                    partials)
            if not np.isnan(cost):
                estimate[good] = cost
                live[good] = cost
                in_live[good] = True
            continue
        if not thin or wanted[good] <= 0.0 or not in_live[good]:
            continue
        depth = min(1.0, traded[good] / (thin_share * wanted[good]))
        if depth >= 1.0:
            continue
        cost = cheapest_cost_of(good, makers_start, makers, inputs_start, inputs_item, inputs_quantity, labour_start, labour_item,
                                labour_quantity, plant_start, plant_item, plant_quantity, plant_hours_start, plant_hours_item,
                                plant_hours_quantity, outputs_start, outputs_item, outputs_quantity, plant_life, live, wages, rate,
                                partials)
        if not np.isnan(cost):
            live[good] = depth * live[good] + (1.0 - depth) * cost
            estimate[good] = live[good]
    return estimate


def _prices_by(names: List[str], prices: Mapping[str, float]) -> np.ndarray:
    return np.array([prices.get(name, np.nan) for name in names], dtype=np.float64)


def cost_estimates(mode: int, recipes: Mapping[str, object], live: Mapping[str, float], wages: Mapping[str, float], rate: float,
                   recent=frozenset(), thin: bool = False, wanted: Mapping[str, float] = None, traded: Mapping[str, float] = None,
                   thin_share: float = 1.0) -> Dict[str, float]:
    """`{good: estimate}` for the goods that have one, in the order the estimates were made (input-depth order); see `costed_goods`. `live`
    is read, not changed. A price in `live` that is NaN counts as none."""
    tables = tables_of(recipes)
    goods = tables.goods
    live_array = _prices_by(goods, live)
    estimate = costed_goods(
        mode, tables.order, tables.makers_start, tables.makers, *tables.inputs, *tables.labour, *tables.plant_goods, *tables.plant_labour,
        *tables.outputs, tables.plant_life, live_array, np.array([name in live for name in goods], dtype=np.bool_),
        _prices_by(tables.trades, wages), float(rate), np.array([name in recent for name in goods], dtype=np.bool_), bool(thin),
        np.array([(wanted or {}).get(name, 0.0) for name in goods], dtype=np.float64),
        np.array([(traded or {}).get(name, 0.0) for name in goods], dtype=np.float64), float(thin_share))
    found = tables.order[~np.isnan(estimate[tables.order])]
    return {goods[good]: float(estimate[good]) for good in found.tolist()}
