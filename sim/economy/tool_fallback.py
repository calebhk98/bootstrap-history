"""What a run does when the tool its workers wear is short: draw the next tool the trade's basket names, then
work by hand. Each step carries the extra hours per run it asks (the data's `tool_hours_factor`). A tool
shortage alone never stops a run. Nothing here names a good or a trade."""
import math
from typing import Dict, Mapping, Optional, Tuple

from .types import GoodId, Recipe, TradeId


def draws(recipe: Recipe, held: Mapping[GoodId, float], runs: float) -> Tuple[Dict[GoodId, float], Dict[TradeId, float]]:
    """(tools used up, extra hours by trade) for `runs` runs of `recipe` given the stock `held`: each wear good
    first, the runs it cannot cover by the next fallback that is held, the rest by hand."""
    used: Dict[GoodId, float] = {}
    extra_hours: Dict[TradeId, float] = {}
    for good, per_run in sorted(recipe.tool_wear.items()):
        first = min(runs, held.get(good, 0.0) / per_run) if per_run > 0.0 else runs
        if first > 0.0:
            used[good] = used.get(good, 0.0) + first * per_run
        remaining = runs - first
        for step in recipe.tool_fallbacks.get(good, ()):
            if remaining <= 1e-12 * max(1.0, runs):
                break
            if step.good and step.units_per_run > 0.0:
                covered = min(remaining, max(0.0, held.get(step.good, 0.0) - used.get(step.good, 0.0)) / step.units_per_run)
                if covered > 0.0:
                    used[step.good] = used.get(step.good, 0.0) + covered * step.units_per_run
            elif step.good:
                continue
            else:
                covered = remaining
            if covered > 0.0 and step.hours_factor > 1.0:
                for trade in step.trades:
                    extra_hours[trade] = extra_hours.get(trade, 0.0) + covered * (step.hours_factor - 1.0) * recipe.labour_hours[trade]
            remaining -= max(0.0, covered)
    return used, {trade: hours for trade, hours in extra_hours.items() if math.isfinite(hours) and hours > 0.0}


def shift_unmet_tools(required: Dict[GoodId, float], runs: Mapping[str, float], recipes: Mapping[str, Recipe],
                      ranked: Mapping[GoodId, list], ceilings: Mapping[str, float]) -> None:
    """Move the tool wear a deposit-bound supply cannot meet onto the first fallback good each user draws, in
    place in `required`: where every maker of a tool is held to a ceiling and the runs' wear is more than they
    make, the same share of every user's wear is met by its next tool. Users not held keep their demand."""
    wearing: Dict[GoodId, float] = {}
    for recipe_id, count in runs.items():
        for good, per_run in recipes[recipe_id].tool_wear.items():
            wearing[good] = wearing.get(good, 0.0) + count * per_run
    for good, wear in sorted(wearing.items()):
        makers = ranked.get(good, ())
        if not makers or any(maker not in ceilings for maker in makers) or wear <= 0.0:
            continue
        capacity = math.fsum(ceilings[maker] * recipes[maker].outputs.get(good, 0.0) for maker in makers)
        unmet = min(wear, required.get(good, 0.0) - capacity)
        if unmet <= 0.0:
            continue
        share = unmet / wear
        for recipe_id, count in sorted(runs.items()):
            recipe = recipes[recipe_id]
            per_run = recipe.tool_wear.get(good, 0.0)
            step = next((step for step in recipe.tool_fallbacks.get(good, ()) if step.good), None)
            if per_run > 0.0 and step is not None:
                required[good] -= share * count * per_run
                required[step.good] = required.get(step.good, 0.0) + share * count * step.units_per_run


def value_in_use(recipe: Recipe, good: GoodId, prices: Mapping[GoodId, float], wages: Mapping[TradeId, float]) -> Optional[float]:
    """What one unit of tool `good` is worth to a run of `recipe` against its cheapest substitute: the cost the run
    saves per unit by drawing it instead of the next tool its basket names or working by hand (a later tool's
    price per run plus the extra hours it asks, less the extra hours this tool asks itself). A tool that is the
    first of its wear, or a later one, both have a substitute after them; None when `good` is no tool of the
    recipe, nothing after it can be priced, or a wage is missing."""
    chains = [(good, recipe.tool_wear[good], 0.0, recipe.tool_fallbacks.get(good, ()))] if good in recipe.tool_wear else []
    for first, steps in sorted(recipe.tool_fallbacks.items()):
        for index, step in enumerate(steps):
            if step.good == good and step.units_per_run > 0.0:
                chains.append((first, step.units_per_run, _extra_hours_cost(recipe, step, wages), steps[index + 1:]))
    values = []
    for _first, units, own_hours_cost, later in chains:
        alternatives = [cost for cost in (_step_cost(recipe, step, prices, wages) for step in later) if cost is not None]
        if own_hours_cost is None or not alternatives:
            continue
        values.append(max(0.0, min(alternatives) - own_hours_cost) / units)
    return max(values) if values else None


def _extra_hours_cost(recipe: Recipe, step, wages: Mapping[TradeId, float]) -> Optional[float]:
    if any(trade not in wages for trade in step.trades):
        return None
    return math.fsum((step.hours_factor - 1.0) * recipe.labour_hours[trade] * wages[trade] for trade in step.trades
                     if step.hours_factor > 1.0)


def _step_cost(recipe: Recipe, step, prices: Mapping[GoodId, float], wages: Mapping[TradeId, float]) -> Optional[float]:
    """A run's extra cost when the work is covered by `step`: its tool at its price plus its extra hours."""
    hours = _extra_hours_cost(recipe, step, wages)
    if hours is None or (step.good and step.good not in prices):
        return None
    return (step.units_per_run * prices[step.good] if step.good else 0.0) + hours
