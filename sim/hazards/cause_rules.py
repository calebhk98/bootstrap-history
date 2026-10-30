"""What each quantity an event's cause can name is, worked out from the facts its owner publishes.

Each rule takes written-out facts and answers a number, or None when the fact is not yet measured (the cause then neither
holds nor fails). The readers in `cause_quantities` fetch the facts."""
from typing import Any, Dict, List, Optional, Sequence

# a floor under the worst welfare, so a body of people with nothing does not make the spread infinite
WORST_WELFARE_FLOOR = 0.01


def funded_share(need: float, unfunded: float) -> float:
    """Share of what the state needs that its revenue covers; 1 when it needs nothing."""
    return 1.0 if need <= 0.0 else max(0.0, 1.0 - unfunded / need)


def army_share_of_wanted(wanted: float, under_arms: float) -> float:
    """Soldiers kept over the force the state's threat calls for; 1 when it wants none."""
    return 1.0 if wanted <= 0.0 else under_arms / wanted


def territory_share(tiles_now: Sequence[str], tiles_at_start: Sequence[str]) -> float:
    """Share of the tiles held at the start still held; 1 when none were held."""
    return 1.0 if not tiles_at_start else len(set(tiles_now) & set(tiles_at_start)) / len(tiles_at_start)


def output_hours_per_head(output_hours: Optional[float], people: Optional[float]) -> Optional[float]:
    if output_hours is None or people is None or people <= 0.0:
        return None
    return output_hours / people


def measured_welfares(rows: Sequence[Dict[str, Any]]) -> List[float]:
    """Welfare of the free (not bonded) home bodies of people that have people and a yearly welfare measured."""
    return [row["welfare"] for row in rows
            if not row["bonded"] and row["members"] > 0.0 and row["welfare"] is not None]


def lowest_stratum_welfare(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    return min(measured_welfares(rows), default=None)


def stratum_welfare_spread(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    """Welfare of the best-off free body of people over the worst-off: how unequal living standards are."""
    welfares = measured_welfares(rows)
    if not welfares:
        return None
    return max(welfares) / max(min(welfares), WORST_WELFARE_FLOOR)


def elite_share_vs_opening(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    """The propertied strata's share of home people now, over the share the opening split gave them."""
    people = sum(row["members"] for row in rows)
    opening_total = sum(row["opening_share"] for row in rows)
    opening_elite = sum(row["opening_share"] for row in rows if row["property_share"] > 0.0)
    if people <= 0.0 or opening_total <= 0.0 or opening_elite <= 0.0:
        return None
    elite = sum(row["members"] for row in rows if row["property_share"] > 0.0)
    return (elite / people) / (opening_elite / opening_total)
