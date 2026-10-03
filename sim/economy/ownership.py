"""Who owns what on a tile: property income paid to the tile's owner cohort is shared by ownership share.

`owner_cohort(record, tile)` is the cohort named as payee and nominal owner; `spread(record, payments)`
re-splits dividends and rents paid to such an owner across all of the tile's cohorts.
"""
from typing import Dict, List, Optional, Sequence

from .households_cohort import cohort_id, distribute_property_income
from .types import AgentId, TileId, Transfer

SPREAD_PURPOSES = ("dividend", "rent")      # payments that are income from owning something


def richest_class(cohorts, tile: TileId) -> Optional[int]:
    """Income class of the tile's richest cohort, or None where the tile has none."""
    return max((cohort.income_class for cohort in cohorts if cohort.tile == tile), default=None)


def owner_cohort(record, tile: TileId) -> Optional[AgentId]:
    income_class = richest_class(record.cohorts.values(), tile)
    return None if income_class is None else cohort_id(tile, income_class)


def spread(record, payments: Sequence[Transfer]) -> List[Transfer]:
    """Dividends and rents paid to a cohort become payments to every cohort of its tile, each by its
    ownership share; other payments pass through unchanged."""
    result: List[Transfer] = []
    for payment in payments:
        owner = record.cohorts.get(payment.payee)
        if owner is None or payment.purpose not in SPREAD_PURPOSES:
            result.append(payment)
            continue
        tile_cohorts = sorted((cohort for cohort in record.cohorts.values() if cohort.tile == owner.tile),
                              key=lambda cohort: cohort.agent_id)
        shares: Dict[AgentId, float] = distribute_property_income(tile_cohorts, payment.amount)
        paid = [Transfer(payment.payer, agent, payment.currency, amount, payment.purpose)
                for agent, amount in shares.items() if amount > 0.0]
        result.extend(paid or [payment])
    return result
