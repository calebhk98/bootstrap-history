"""Readers of simulation state an event's causes can name (Complaints/266), beyond the first few in `event_causes`.

Each reader takes the game and returns a number, or None when the state it reads is not yet measured
(the cause then neither holds nor fails: the event stands as written).
"""
from typing import Any, List, Optional

# a floor under the worst welfare, so a body of people with nothing does not make the spread infinite
WORST_WELFARE_FLOOR = 0.01


def food_supply_ratio(sim: Any, node: Optional[str] = None) -> Optional[float]:
    """Calories available over calories needed in the last demographic year; 1 is need exactly met."""
    flows = getattr(sim, "_last_demographic_step", None)
    return None if flows is None else float(flows.nutrition_ratio)


def _free_home_strata(sim: Any) -> List[Any]:
    """Home bodies of people that are free (not bonded) and have had a yearly welfare measured."""
    return [stratum for stratum in sim.actors.of_kind("stratum")
            if stratum.record.country is None and stratum.record.exited_year is None
            and not stratum.record.plan.get("bonded") and stratum.record.members > 0.0
            and stratum.record.welfare_reference > 0.0]


def lowest_stratum_welfare(sim: Any, node: Optional[str] = None) -> Optional[float]:
    """The welfare ratio (resources over the food bill) of the worst-off free body of people."""
    strata = _free_home_strata(sim)
    return min((stratum.record.welfare for stratum in strata), default=None)


def stratum_welfare_spread(sim: Any, node: Optional[str] = None) -> Optional[float]:
    """Welfare of the best-off free body of people over the worst-off: how unequal living standards are."""
    welfares = [stratum.record.welfare for stratum in _free_home_strata(sim)]
    if not welfares:
        return None
    return max(welfares) / max(min(welfares), WORST_WELFARE_FLOOR)


def coin_metal_kept(sim: Any, node: Optional[str] = None) -> float:
    """Share of the opening metal the state's coin still holds after every cut so far."""
    return float(sim.state_treasury().record.coin_metal_kept)


def elite_share_vs_opening(sim: Any, node: Optional[str] = None) -> Optional[float]:
    """The propertied strata's share of home people now, over the share the opening split gave them."""
    strata = [stratum for stratum in sim.actors.of_kind("stratum")
              if stratum.record.country is None and stratum.record.exited_year is None]
    people = sum(stratum.record.members for stratum in strata)
    opening_total = sum(float(stratum.record.plan.get("share", 0.0)) for stratum in strata)
    opening_elite = sum(float(stratum.record.plan.get("share", 0.0)) for stratum in strata
                        if float(stratum.record.plan.get("property_share", 0.0)) > 0.0)
    if people <= 0.0 or opening_total <= 0.0 or opening_elite <= 0.0:
        return None
    elite = sum(stratum.record.members for stratum in strata
                if float(stratum.record.plan.get("property_share", 0.0)) > 0.0)
    return (elite / people) / (opening_elite / opening_total)
