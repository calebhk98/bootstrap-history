"""Selections of loan rows by agent name, for the rules that pick loans out of the table (which may be sold, which a title pledges)."""
from typing import Collection, Dict, List

import numpy

from .columns import NO_TILE
from .store import LoanStore


def agent_numbers(store: LoanStore, names: Collection[str]) -> List[int]:
    """The store's numbers of those of `names` that appear among its loans' agents."""
    found = (store.agents.find(name) for name in names)
    return [number for number in found if number is not None]


def lent_by(store: LoanStore, names: Collection[str]) -> numpy.ndarray:
    """A boolean per row: the loan's lender is one of `names`."""
    return numpy.isin(store.table.lender[:len(store)], agent_numbers(store, names))


def owed_by(store: LoanStore, names: Collection[str]) -> numpy.ndarray:
    """A boolean per row: the loan's borrower is one of `names`."""
    return numpy.isin(store.table.borrower[:len(store)], agent_numbers(store, names))


def tradable(store: LoanStore, banks: Collection[str], cohorts: Collection[str], floor: float) -> numpy.ndarray:
    """A boolean per row: a claim a lender may sell (secondary_trade.tradable): not a deposit with a bank, not a household's own debt,
    pledging no land, and with more than `floor` of principal."""
    table, count = store.table, len(store)
    return (~owed_by(store, banks) & ~owed_by(store, cohorts) & (table.collateral_tile[:count] == NO_TILE) & (table.principal[:count] > floor))


def pledged_shares(store: LoanStore, holder: str, tile: str) -> List[float]:
    """The share of `tile` each loan of `holder` pledges, in table order, as Python floats."""
    rows = store.rows_of(borrower=holder)
    number = store.tiles.find(tile)
    if number is None or not len(rows):
        return []
    table = store.table
    return table.collateral_share[rows[table.collateral_tile[rows] == number]].tolist()


def pledges_by_title(store: LoanStore) -> Dict[tuple, List[float]]:
    """{(holder, tile): the shares its loans pledge in table order} for every loan that pledges a tile."""
    table, count = store.table, len(store)
    rows = numpy.nonzero(table.collateral_tile[:count] != NO_TILE)[0]
    shares: Dict[tuple, List[float]] = {}
    names, tiles = store.agents.name_list, store.tiles.name_list
    for borrower, tile, share in zip(table.borrower[rows].tolist(), table.collateral_tile[rows].tolist(), table.collateral_share[rows].tolist()):
        shares.setdefault((names[borrower], tiles[tile]), []).append(share)
    return shares
