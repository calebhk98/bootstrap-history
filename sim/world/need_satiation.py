"""A need with a physical limit per head stops absorbing budget once it is met.

A durable ornament is worn out and lost at a rate; households do not turn a
fixed share of income into new metal without end. A need may declare
`satiation_per_capita_per_year` (in its own unit); units above that are not
bought, and the spending they would have taken goes to the needs still short,
in proportion to their budget weights.
"""
from typing import Any, Dict, Mapping

SATIATION_FIELD = "satiation_per_capita_per_year"


def apply_satiation(need_units: Dict[str, float], price_index: Mapping[str, float],
                    needs: Mapping[str, Mapping[str, Any]], population: float) -> None:
    """Cap each satiable need's units at its limit and move the freed spending, in place."""
    capped = set()
    while True:
        newly = {need_id for need_id, units in need_units.items()
                 if need_id not in capped and needs[need_id].get(SATIATION_FIELD) is not None
                 and units > needs[need_id][SATIATION_FIELD] * population}
        if not newly:
            return
        freed = 0.0
        for need_id in newly:
            limit = needs[need_id][SATIATION_FIELD] * population
            freed += (need_units[need_id] - limit) * price_index[need_id]
            need_units[need_id] = limit
        capped |= newly
        open_needs = [need_id for need_id in need_units if need_id not in capped]
        weight_total = sum(needs[need_id]["surplus_budget_share"] for need_id in open_needs)
        if weight_total <= 0.0:
            return   # every need is satiated: the rest of income is not spent on goods
        for need_id in open_needs:
            need_units[need_id] += (freed * needs[need_id]["surplus_budget_share"]
                                    / weight_total / price_index[need_id])
