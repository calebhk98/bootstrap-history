"""What a household makes for itself: hours nobody hired go into its own plot.

Most people in a pre-industrial economy grew much of their own food outside any market. A cohort's
unsold hours work the land-only recipes (no bought inputs) that serve a need with a subsistence floor,
on its own tile at the tile's fertility, up to that floor. What it grows it eats; only the rest of its
needs go to market. A cohort that went short of a floor keeps back from the labour market the
hours that grow its own-plot plan (the shortfall, kept up and eased off over the years), however high
the wage: money does not feed a family where nobody sells food. The land a cohort works is not yet drawn from the tile's arable area, which is
plentiful against what people can work by hand.
"""
import dataclasses
import math
from typing import Dict, List, Mapping, Sequence, Tuple

from sim.constants import declare

from .households_basket import Basket
from .households_cohort import Cohort
from .types import EDGE_PRODUCTION, AgentId, GoodId, GoodsMove, LabourOffer, Recipe

OWN_PLAN_RELEASE_SHARE_PER_YEAR = declare(
    "OWN_PLAN_RELEASE_SHARE_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of the own-plot plan dropped a year", source=None, confidence="D",
    why="A household that went short grows the shortfall itself and keeps doing so, easing back as it "
        "tries the market again. How fast families trusted markets again after a dearth is not measured; "
        "stands in for their expectations about supply.")

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


def hours_for_own_plan(cohort: Cohort, options: Mapping[str, List[Option]], fertility: float) -> float:
    """Hours that grow the cohort's own-plot plan (need units by need) at this fertility."""
    if fertility <= 0.0:
        return 0.0
    hours = 0.0
    for need_id, units in sorted(cohort.own_plan_by_need.items()):
        rows = options.get(need_id)
        if rows and units > 0.0:
            hours += units * rows[0][0] / fertility
    return hours


def next_own_plan(plan: Mapping[str, float], unmet: Mapping[str, float]) -> Dict[str, float]:
    """Next year's plan: what it planned to grow, eased off so the household tries the market again,
    plus what it went short of this year."""
    kept = 1.0 - OWN_PLAN_RELEASE_SHARE_PER_YEAR
    needs = set(plan) | {need for need, units in unmet.items() if units > 0.0}
    nxt = {need: plan.get(need, 0.0) * kept + max(0.0, unmet.get(need, 0.0)) for need in sorted(needs)}
    return {need: units for need, units in nxt.items() if units > 1e-9}


def withhold_hours(offers: Sequence[LabourOffer], hours_by_worker: Mapping[AgentId, float]
                   ) -> Tuple[List[LabourOffer], Dict[AgentId, float]]:
    """(offers with each worker's hours cut in proportion to what it keeps back, hours kept by worker)."""
    offered: Dict[AgentId, float] = {}
    for offer in offers:
        offered[offer.worker] = offered.get(offer.worker, 0.0) + offer.hours
    kept = {worker: min(hours, offered.get(worker, 0.0)) for worker, hours in hours_by_worker.items()
            if hours > 0.0 and offered.get(worker, 0.0) > 0.0}
    cut = [offer if offer.worker not in kept else
           dataclasses.replace(offer, hours=offer.hours * (1.0 - kept[offer.worker] / offered[offer.worker]))
           for offer in offers]
    return cut, kept
