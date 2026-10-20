"""Debt relief a state decrees on a tile (a seisachtheia, a jubilee): the tile's households owe nothing more.

Every term loan whose borrower is a cohort of the tile is cancelled and the lender books the loss (principal
and arrears) as it would a default, except that no title is taken: the borrowers keep their land. Rent
arrears of tenants on the tile are forgiven too. The state's choice reaches the economy as the tiles in
`YearInputs.debt_relief_tiles`.
"""
from typing import Dict, Iterable

from .types import TileId


def forgive(record, tiles: Iterable[TileId]) -> Dict[str, float]:
    """Cancel household debts and tenancy arrears on the tiles. Returns the principal and arrears written off."""
    relieved = set(tiles)
    borrowers = {cohort.agent_id for cohort in record.cohorts.values() if cohort.tile in relieved}
    written_off = {"principal": 0.0, "arrears": 0.0, "rent_arrears": 0.0}
    if not relieved:
        return written_off
    kept = []
    for loan in record.loans:
        if loan.borrower not in borrowers:
            kept.append(loan)
            continue
        written_off["principal"] += loan.principal
        written_off["arrears"] += loan.arrears
        record.credit_losses[loan.lender] = record.credit_losses.get(loan.lender, 0.0) + loan.principal + loan.arrears
    record.loans = kept
    for tile in relieved:
        for row in getattr(record, "tenancies", {}).get(tile, ()):
            written_off["rent_arrears"] += row["arrears"]
            row["arrears"] = 0.0
    return written_off


def indebted_tiles(record) -> list:
    """Tiles where a household cohort owes a term loan, sorted: the tiles a state could relieve."""
    tile_of = {cohort.agent_id: cohort.tile for cohort in record.cohorts.values()}
    return sorted({tile_of[loan.borrower] for loan in record.loans if loan.borrower in tile_of})
