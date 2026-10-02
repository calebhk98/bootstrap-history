"""What a household makes for itself: hours nobody hired go into its own plot.

Most people in a pre-industrial economy grew much of their own food outside any market. A cohort's
unsold hours work the land-only recipes (no bought inputs) that serve a need with a subsistence floor,
on its own tile at the tile's fertility, up to that floor. What it grows it eats; only the rest of its
needs go to market. The land a cohort works is not yet drawn from the tile's arable area, which is
plentiful against what people can work by hand.
"""
import math
from typing import Dict, List, Mapping, Tuple

from .households_basket import Basket
from .households_cohort import Cohort
from .types import EDGE_PRODUCTION, GoodId, GoodsMove, Recipe

Option = Tuple[float, str, GoodId, float]      # (hours per need unit, recipe id, good, need units per unit)


def own_production_options(recipes: Mapping[str, Recipe], land_per_run: Mapping[str, float],
                           basket: Basket) -> Dict[str, List[Option]]:
    """For each need, the land-only recipes whose output serves it, fewest hours first. Only needs with a
    floor where the cohort lives are grown (own_production reads the cohort's own floors)."""
    options: Dict[str, List[Option]] = {}
    for need in basket.needs:
        rows = []
        for recipe_id, recipe in sorted(recipes.items()):
            hours = math.fsum(recipe.labour_hours.values())
            if recipe.inputs or land_per_run.get(recipe_id, 0.0) <= 0.0 or hours <= 0.0:
                continue
            for good, effect in need.goods:
                made = recipe.outputs.get(good, 0.0)
                if made > 0.0 and effect > 0.0:
                    rows.append((hours / (made * effect), recipe_id, good, effect))
        if rows:
            options[need.need_id] = sorted(rows)
    return options


def own_production(cohort: Cohort, idle_hours: float, options: Mapping[str, List[Option]],
                   recipes: Mapping[str, Recipe], fertility: float, basket: Basket
                   ) -> Tuple[List[GoodsMove], Dict[GoodId, float], Dict[str, float]]:
    """(moves booking what it grew, goods grown, need units grown) for one cohort's idle hours."""
    moves: List[GoodsMove] = []
    grown: Dict[GoodId, float] = {}
    units: Dict[str, float] = {}
    hours_left = max(0.0, idle_hours)
    for need in basket.needs:
        rows = options.get(need.need_id)
        if not rows or hours_left <= 0.0 or fertility <= 0.0:
            continue
        hours_per_unit, recipe_id, good, effect = rows[0]
        floor_units = need.subsistence_per_person * cohort.people
        hours_per_unit = hours_per_unit / fertility
        wanted_hours = floor_units * hours_per_unit
        used = min(hours_left, wanted_hours)
        if used <= 0.0:
            continue
        hours_left -= used
        made_units = used / hours_per_unit
        quantity = made_units / effect
        grown[good] = grown.get(good, 0.0) + quantity
        units[need.need_id] = units.get(need.need_id, 0.0) + made_units
        moves.append(GoodsMove(EDGE_PRODUCTION, cohort.agent_id, good, cohort.tile, quantity, "grown for itself"))
    return moves, grown, units
