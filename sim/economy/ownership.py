"""Who owns what on a tile: property income paid to the tile's owner cohort is shared by ownership share.

`owner_cohort(record, tile)` is the cohort named as payee and nominal owner; `spread(record, payments)`
re-splits dividends across all of the tile's cohorts by ownership share and rents across the tile's title
holders (titles.py).
"""
from typing import Dict, List, Optional, Sequence

from . import shares as producer_shares, titles
from .cohort_store import table_of
from .households_cohort import cohort_id, distribute_property_income
from .types import AgentId, TileId, Transfer

SPREAD_PURPOSES = ("dividend", "rent")      # payments that are income from owning something


def richest_class(cohorts, tile: TileId) -> Optional[int]:
    """Income class of the tile's richest cohort, or None where the tile has none."""
    return max((cohort.income_class for cohort in cohorts if cohort.tile == tile), default=None)


def property_shares(store, cohort_ids: Sequence[AgentId], amount: float) -> Dict[AgentId, float]:
    """`distribute_property_income` for the cohorts named, their ownership shares read from the cohort table `store`."""
    owned = store.floats("ownership_share", store.rows_of(cohort_ids))
    total = sum(owned)
    if total <= 0.0:
        return {cohort_id: 0.0 for cohort_id in cohort_ids}
    return {cohort_id: amount * share / total for cohort_id, share in zip(cohort_ids, owned)}


def owner_cohort(record, tile: TileId) -> Optional[AgentId]:
    income_class = table_of(record.cohorts).richest_class(tile)
    return None if income_class is None else cohort_id(tile, income_class)


def spread(record, payments: Sequence[Transfer], by_tile: Optional[Dict[TileId, list]] = None) -> List[Transfer]:
    """Dividends and rents paid to a cohort become payments to every cohort of its tile, each by its
    ownership share (after the part due to holders of the producer's shares, shares.py); other payments pass
    through unchanged. `by_tile` (empty to begin with) keeps each
    tile's cohorts across calls while the cohorts do not change."""
    result: List[Transfer] = []
    store = table_of(record.cohorts)
    for payment in (part for each in payments for part in producer_shares.split_dividend(record, each)):
        owner_tile = store.tile_of(payment.payee)
        if owner_tile is None or payment.purpose not in SPREAD_PURPOSES:
            result.append(payment)
            continue
        if payment.purpose == "rent":
            paid = [Transfer(payment.payer, holder, payment.currency, amount, payment.purpose)       # rent goes to whoever holds the land
                    for holder, amount in titles.split_among_holders(record, owner_tile, payment.amount).items()]
            result.extend(paid or [payment])
            continue
        tile_cohorts = by_tile.get(owner_tile) if by_tile is not None else None
        if tile_cohorts is None:
            tile_cohorts = sorted(store.ids[row] for row in store.rows_on_tile(owner_tile).tolist())
            if by_tile is not None:
                by_tile[owner_tile] = tile_cohorts
        shares: Dict[AgentId, float] = property_shares(store, tile_cohorts, payment.amount)
        paid = [Transfer(payment.payer, agent, payment.currency, amount, payment.purpose)
                for agent, amount in shares.items() if amount > 0.0]
        result.extend(paid or [payment])
    return result
