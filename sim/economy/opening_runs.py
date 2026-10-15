"""Which recipes make what at the opening, and how many runs of each a year the opening's demand takes.

Final demand plus what the producers of it consume (input-output back to raw materials) fixes the quantity
of every good. Each good is made by the recipe that makes it cheapest per unit (a joint run's cost shared by
the value of the outputs that are wanted); where deposits limit that recipe, or an input only deposits supply,
the rest is made by the next cheapest.
"""
import math
from typing import Dict, List, Mapping, Optional, Tuple

from . import sites, unit_cost
from .types import GoodId, Recipe, TileId

INPUT_OUTPUT_PASSES = 60
INCUMBENT_PASSES = 4          # numerical bound on choosing recipes against the demand they then meet
CEILING_SWEEPS = 6            # numerical bound on carrying a deposit's limit down the chain of recipes that use it


def national_totals(by_tile: Mapping[TileId, Mapping[GoodId, float]]) -> Dict[GoodId, float]:
    total: Dict[GoodId, float] = {}
    for demand in by_tile.values():
        for good, quantity in demand.items():
            total[good] = total.get(good, 0.0) + quantity
    return dict(sorted(total.items()))


def ranked_recipes(recipes: Mapping[str, Recipe], prices: Mapping[GoodId, float], wages: Mapping[str, float],
                   rate: float, required: Optional[Mapping[GoodId, float]] = None) -> Dict[GoodId, List[str]]:
    """The recipes that make each good, cheapest per unit of that good first: a joint run's cost shared among
    its outputs by their value. With `required` (the quantity of each good the opening needs), a run's
    co-product counts only up to what is needed once the runs for the good are made: a by-product nobody wants
    in that quantity is no value to the run, and the good is made another way."""
    costed: Dict[GoodId, List[Tuple[float, str]]] = {}
    for recipe_id, recipe in sorted(recipes.items()):
        cost = (unit_cost.variable_cost_per_run(recipe, prices, wages)
                + unit_cost.capital_charge_per_run(recipe, prices, wages, rate))
        if not math.isfinite(cost):
            continue
        for good, quantity in recipe.outputs.items():
            if quantity <= 0.0:
                continue
            values = _supported_values(recipe, good, prices, required)
            total_value = math.fsum(values.values())
            share = values[good] / total_value if total_value > 0.0 else 1.0 / len(recipe.outputs)
            costed.setdefault(good, []).append((cost * share / quantity, recipe_id))
    return {good: [recipe_id for _cost, recipe_id in sorted(rows)] for good, rows in sorted(costed.items())}


def first_choices(ranked: Mapping[GoodId, List[str]]) -> Dict[GoodId, str]:
    """The recipe each good is made by when nothing limits it."""
    return {good: choices[0] for good, choices in ranked.items()}


def _supported_values(recipe: Recipe, good: GoodId, prices: Mapping[GoodId, float],
                      required: Optional[Mapping[GoodId, float]]) -> Dict[GoodId, float]:
    """Value of one run's outputs when runs are made for `good`: each output at its price, a co-product only up
    to the quantity the opening needs of it (all of it when `required` is not given)."""
    values = {output: quantity * prices.get(output, 0.0) for output, quantity in recipe.outputs.items()}
    if required is None or recipe.outputs[good] <= 0.0 or len(values) == 1:
        return values
    runs = required.get(good, 0.0) / recipe.outputs[good]
    if runs <= 0.0:
        return values
    for output, quantity in recipe.outputs.items():
        if output != good:
            values[output] = min(quantity, required.get(output, 0.0) / runs) * prices.get(output, 0.0)
    return values


def run_ceilings(recipes: Mapping[str, Recipe], by_limits) -> Dict[str, float]:
    """Most runs a year the deposits allow of each recipe that depends on them: a site-bound recipe with declared
    limits is held to their sum, and a recipe that uses an input only such recipes make is held to the runs that
    input's supply feeds (each user is shown the whole supply). A recipe nothing limits has no entry."""
    ceilings: Dict[str, float] = {}
    for recipe_id, recipe in recipes.items():
        if sites.is_sited(recipe, by_limits):
            ceilings[recipe_id] = math.fsum(limit.capacity_runs_per_year for limit in by_limits[recipe_id].values())
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id, recipe in recipes.items():
        for good, quantity in recipe.outputs.items():
            if quantity > 0.0:
                makers.setdefault(good, []).append(recipe_id)
    for _sweep in range(CEILING_SWEEPS):
        changed = False
        for good, makers_of in makers.items():
            if not all(maker in ceilings for maker in makers_of):
                continue                              # something unlimited also makes it
            supply = math.fsum(ceilings[maker] * recipes[maker].outputs[good] for maker in makers_of)
            for recipe_id, recipe in recipes.items():
                needed = recipe.inputs.get(good, 0.0)
                if needed > 0.0 and ceilings.get(recipe_id, math.inf) > supply / needed * (1.0 + 1e-12):
                    ceilings[recipe_id] = supply / needed
                    changed = True
        if not changed:
            break
    return ceilings


def required_quantities(final_by_tile, runs: Mapping[str, float], recipes: Mapping[str, Recipe]) -> Dict[GoodId, float]:
    """What the opening needs of each good a year: final demand, and what `runs` use up as inputs and plant wear."""
    required = dict(national_totals(final_by_tile))
    for recipe_id, count in runs.items():
        recipe = recipes[recipe_id]
        for good, quantity in recipe.inputs.items():
            required[good] = required.get(good, 0.0) + count * quantity
        if recipe.plant_life_years > 0.0:
            for good, quantity in recipe.plant_goods.items():
                required[good] = required.get(good, 0.0) + count * quantity / recipe.plant_life_years
    return required


def required_runs(final_by_tile, ranked: Mapping[GoodId, List[str]], recipes: Mapping[str, Recipe],
                  ceilings: Optional[Mapping[str, float]] = None) -> Dict[str, float]:
    """Runs a year of each recipe that meet final demand and every chosen recipe's own inputs and plant wear
    (a fixed point of the input-output system). A good takes its cheapest recipe up to that recipe's ceiling,
    then the next, so what a deposit cannot feed is made another way; a joint run's other outputs count toward
    their own goods."""
    ceilings = ceilings or {}
    runs: Dict[str, float] = {}
    for _ in range(INPUT_OUTPUT_PASSES):
        required = required_quantities(final_by_tile, runs, recipes)
        updated: Dict[str, float] = {}
        for good, quantity in sorted(required.items()):
            remaining = quantity
            for recipe_id in ranked.get(good, ()):
                if quantity <= 0.0:
                    break
                made = recipes[recipe_id].outputs.get(good, 0.0)
                if made <= 0.0:
                    continue
                runs_now = max(updated.get(recipe_id, 0.0), min(remaining / made, ceilings.get(recipe_id, math.inf)))
                updated[recipe_id] = runs_now
                remaining = quantity - runs_now * made
                if remaining <= 1e-9 * quantity:
                    break
        if all(abs(updated.get(key, 0.0) - runs.get(key, 0.0)) <= 1e-9 * max(1.0, updated.get(key, 0.0))
               for key in set(updated) | set(runs)):
            return updated
        runs = updated
    return runs
