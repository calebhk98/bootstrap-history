"""The cost of managing land through tenants: a lessor's overseers and lost effort rise with the number of
tenancies it holds, faster than the rent they bring.

A lessor with one tenancy supervises it itself. Each tenancy beyond the first takes a further share of every
tenancy's rent for stewards (paid to the tile's poorest cohort, whose members they are drawn from), so total
cost grows with the square of the tenancies. Where the cost eats all the rent, the tenancy is worth nothing
to the lessor and the tenant holds the land outright.
"""
from typing import Dict, Mapping

from sim.constants import declare

from .types import AgentId

COST_SHARE_PER_EXTRA_TENANCY = declare(
    "TENANCY_MANAGEMENT_COST_SHARE", 0.01, kind="temporary_heuristic",
    unit="share of a tenancy's rent for each other tenancy the lessor holds",
    source=None, confidence="D",
    why="Overseers and lost effort rise with the number of tenancies a lessor holds; the rate stands in for "
        "supervision and distance, which are not modelled (no overseer staff, no travel between holdings).",
    retire="538 overseer staff and distance costs")


def tenancies_by_lessor(tenancies: Mapping) -> Dict[AgentId, int]:
    count: Dict[AgentId, int] = {}
    for rows in tenancies.values():
        for row in rows:
            count[row["lessor"]] = count.get(row["lessor"], 0) + 1
    return count


def cost_share(tenancy_count: int, share_per_extra: float = COST_SHARE_PER_EXTRA_TENANCY) -> float:
    """The share of each tenancy's rent a lessor with this many tenancies spends on managing them (0..1)."""
    return min(1.0, max(0, tenancy_count - 1) * share_per_extra)
