"""The disease burden of a civilisation from the technologies it holds, as a function of the weights it is given."""
from typing import Mapping

from sim.world import demography


def burden_from_holdings(weight_by_tech: Mapping[str, float], held_share_by_tech: Mapping[str, float]) -> float:
    """1.0 is the full pre-industrial infectious environment, 0.0 every disease technology fully held. Each technology
    removes its share of the total weight, scaled by how much of it counts (all of a built work, the people served
    for a work with coverage). Clamped to [0, 1]; with no weight at all the burden stays pre-industrial."""
    total_weight = sum(weight_by_tech.values())
    if total_weight <= 0.0:
        return demography.PRE_INDUSTRIAL_DISEASE_BURDEN
    unlocked_weight = sum(weight * held_share_by_tech.get(tech_id, 0.0) for tech_id, weight in weight_by_tech.items())
    return max(0.0, min(1.0, 1.0 - unlocked_weight / total_weight))
