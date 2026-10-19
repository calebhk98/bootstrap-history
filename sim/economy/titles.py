"""Land titles: who holds the right to a tile's land rent, and who works land under a holder.

`record.titles` maps tile -> holder -> share of the tile's land (shares sum to at most one; the rest is
held by nobody, abandoned). A holder is any actor: a cohort, a firm, a state. The opening seeds each tile's
titles from its cohorts' ownership shares, so rent flows as before until a title moves. A title moves by
foreclosure: a loan pledges a share, and on default the share passes to the lender while the borrower's
family stays on it as a tenant (`record.tenancies`: tile -> rows of tenant, lessor, share, rent arrears).
Reads fall back on ownership shares for a record that has no titles yet.
"""
from typing import Dict, List, Mapping

from .types import AgentId, CurrencyId, TileId, Transfer

EPSILON = 1e-9


def seed(record) -> None:
    """Each tile's titles start as its cohorts' ownership shares."""
    record.titles = {}
    for cohort in sorted(record.cohorts.values(), key=lambda cohort: cohort.agent_id):
        record.titles.setdefault(cohort.tile, {})[cohort.agent_id] = cohort.ownership_share
    for tile, held in record.titles.items():
        total = sum(held.values())
        record.titles[tile] = {holder: share / total for holder, share in held.items()} if total > 0.0 else {}


def shares(record, tile: TileId) -> Dict[AgentId, float]:
    """Holder -> share of the tile's land (below one in total when part of it is abandoned)."""
    held = getattr(record, "titles", {}).get(tile)
    if held:
        return dict(held)
    return {cohort.agent_id: cohort.ownership_share for cohort in record.cohorts.values() if cohort.tile == tile}


def holding(record, tile: TileId, holder: AgentId) -> float:
    return shares(record, tile).get(holder, 0.0)


def pledged(record, holder: AgentId, tile: TileId) -> float:
    """The share of its title on `tile` the holder has pledged to loans still owed."""
    return sum(loan.collateral_share for loan in record.loans
               if loan.borrower == holder and loan.collateral_tile == tile)


def free_share(record, holder: AgentId, tile: TileId) -> float:
    return max(0.0, holding(record, tile, holder) - pledged(record, holder, tile))


def _held(record, tile: TileId) -> Dict[AgentId, float]:
    if not getattr(record, "titles", None):
        record.titles = {}
    if not record.titles.get(tile):
        record.titles[tile] = shares(record, tile)
    return record.titles[tile]


def _add_tenancy(record, tile: TileId, tenant: AgentId, lessor: AgentId, share: float) -> None:
    if not hasattr(record, "tenancies"):
        record.tenancies = {}
    rows: List[dict] = record.tenancies.setdefault(tile, [])
    for row in rows:
        if row["tenant"] == tenant and row["lessor"] == lessor:
            row["share"] += share
            return
    rows.append({"tenant": tenant, "lessor": lessor, "share": share, "arrears": 0.0})


def foreclose(record, loan) -> float:
    """The loan defaulted: its pledged share passes from borrower to lender and the borrower stays on it as
    a tenant. Returns the value of the collateral the lender took (the loan's collateral value, pro rata to
    the share the borrower still held)."""
    tile, pledge = loan.collateral_tile, loan.collateral_share
    if not tile or pledge <= EPSILON or loan.lender == loan.borrower:
        return 0.0
    held = _held(record, tile)
    moved = min(pledge, held.get(loan.borrower, 0.0))
    if moved <= EPSILON:
        return 0.0
    held[loan.borrower] -= moved
    if held[loan.borrower] <= EPSILON:
        del held[loan.borrower]
    held[loan.lender] = held.get(loan.lender, 0.0) + moved
    _add_tenancy(record, tile, loan.borrower, loan.lender, moved)
    return loan.collateral_value * moved / pledge


def release(record, tile: TileId, lessor: AgentId, share: float) -> None:
    """Abandoned land: the lessor's title on `share` of the tile goes back to no holder."""
    held = _held(record, tile)
    left = held.get(lessor, 0.0) - share
    if left <= EPSILON:
        held.pop(lessor, None)
    else:
        held[lessor] = left


def tenant_share(record, tile: TileId, tenant: AgentId) -> float:
    return sum(row["share"] for row in getattr(record, "tenancies", {}).get(tile, ()) if row["tenant"] == tenant)


def top_holder_share(record, tile: TileId) -> float:
    """The largest holder's share of the land that has a holder."""
    held = shares(record, tile)
    total = sum(held.values())
    return max(held.values()) / total if total > 0.0 else 0.0


def settle_tenancies(record, currency: CurrencyId, arable_by_tile: Mapping[TileId, float]) -> List[Transfer]:
    """Each tenant pays its lessor the tile's rent on the share it works, and any arrears, as far as its cash
    goes. A tenant more than a year's rent behind has left the land: the lessor's title on it goes back to
    nobody. Returns the payments."""
    payments: List[Transfer] = []
    if not getattr(record, "tenancies", None):
        return payments
    cash: Dict[AgentId, float] = {}
    for tile, rows in sorted(record.tenancies.items()):
        rent = record.land_rent.get(tile, 0.0) * arable_by_tile.get(tile, 0.0)
        kept = []
        for row in rows:
            tenant = row["tenant"]
            if tenant not in cash:
                cash[tenant] = max(0.0, record.book.balance(tenant, currency))
            due = rent * row["share"]
            owed = due + row["arrears"]
            paid = min(owed, cash[tenant])
            if paid > 0.0:
                cash[tenant] -= paid
                payments.append(Transfer(tenant, row["lessor"], currency, paid, "tenant_rent"))
            row["arrears"] = owed - paid
            if due > 0.0 and row["arrears"] > due:
                release(record, tile, row["lessor"], row["share"])
            else:
                kept.append(row)
        record.tenancies[tile] = kept
    record.tenancies = {tile: rows for tile, rows in record.tenancies.items() if rows}
    return payments
