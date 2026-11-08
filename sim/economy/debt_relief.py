"""Debt relief a state decrees on a tile (a seisachtheia, a jubilee): the tile's households owe nothing more.

Every term loan whose borrower is a cohort of the tile is cancelled and the lender books the loss (principal
and arrears) as it would a default, except that no title is taken: the borrowers keep their land. Rent
arrears of tenants on the tile are forgiven too. The state's choice reaches the economy as the tiles in
`EconomyYearInputs.debt_relief_tiles`.
"""
from typing import Dict, Iterable

import numpy

from . import titles
from .types import TileId


def forgive(record, tiles: Iterable[TileId]) -> Dict[str, float]:
    """Cancel household debts and tenancy arrears on the tiles. Returns the principal and arrears written off."""
    relieved = set(tiles)
    borrowers = {cohort.agent_id for cohort in record.cohorts.values() if cohort.tile in relieved}
    written_off = {"principal": 0.0, "arrears": 0.0, "rent_arrears": 0.0}
    if not relieved:
        return written_off
    store = record.credit.contracts.loan_store
    numbers = [store.agents.find(name) for name in sorted(borrowers)]
    count = len(store)
    relieved_rows = numpy.isin(store.table.borrower[:count], [number for number in numbers if number is not None])
    rows = numpy.nonzero(relieved_rows)[0]
    for lender, principal, arrears in zip(store.table.lender[rows].tolist(), store.table.principal[rows].tolist(),
                                          store.table.arrears[rows].tolist()):
        written_off["principal"] += principal
        written_off["arrears"] += arrears
        record.credit.add_loss(store.agent_name(lender), principal + arrears)
    store.retain(~relieved_rows)
    for tile in relieved:
        written_off["rent_arrears"] += titles.forgive_rent_arrears(record.land, tile)
    return written_off


def indebted_tiles(record) -> list:
    """Tiles where a household cohort owes a term loan, sorted: the tiles a state could relieve."""
    tile_of = {cohort.agent_id: cohort.tile for cohort in record.cohorts.values()}
    store = record.credit.contracts.loan_store
    borrowers = {store.agent_name(number) for number in numpy.unique(store.table.borrower[:len(store)]).tolist()}
    return sorted({tile_of[borrower] for borrower in borrowers if borrower in tile_of})
