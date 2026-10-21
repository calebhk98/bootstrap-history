"""What a run does when the tool its workers wear is short: draw the next tool the trade's basket names, then
work by hand. Each step carries the extra hours per run it asks (the data's `tool_hours_factor`). A tool
shortage alone never stops a run. Nothing here names a good or a trade."""
import math
from typing import Dict, Mapping, Tuple

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
