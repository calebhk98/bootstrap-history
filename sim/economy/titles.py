"""Land titles: who holds the right to a tile's land rent, and who works land under a holder.

`record.titles` maps tile -> holder -> share of the tile's land (shares sum to at most one; the rest is
held by nobody, abandoned). A holder is any actor: a cohort, a firm, a state. The opening seeds each tile's
titles from its cohorts' ownership shares, so rent flows as before until a title moves. A title moves by
foreclosure: a loan pledges a share, and on default the share passes to the lender while the borrower's
family stays on it as a tenant (`record.tenancies`: tile -> rows of tenant, lessor, share, rent arrears).
Reads fall back on ownership shares for a record that has no titles yet.
"""
from typing import Dict, List, Mapping, Optional

from . import titles_management
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


def let_out_share(record, tile: TileId, lessor: AgentId) -> float:
    return sum(row["share"] for row in getattr(record, "tenancies", {}).get(tile, ()) if row["lessor"] == lessor)


def lease(record, tile: TileId, tenant: AgentId, lessor: AgentId, share: float) -> float:
    """A tenancy made in the market, not by default: the lessor lets `share` of the tile to the tenant, no more than
    the title it holds and has not pledged or already let out. The title stays with the lessor. Returns the share let."""
    if tenant == lessor or share <= EPSILON:
        return 0.0
    let = min(share, free_share(record, lessor, tile) - let_out_share(record, tile, lessor))
    if let <= EPSILON:
        return 0.0
    _add_tenancy(record, tile, tenant, lessor, let)
    return let


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


def pass_title(record, tile: TileId, giver: AgentId, receiver: AgentId, share: float) -> float:
    """`share` of the tile's land passes from giver to receiver, no more than the giver holds. A receiver that
    was the giver's tenant on the tile now holds that much outright, so its tenancy under the giver shrinks.
    Returns the share moved."""
    held = _held(record, tile)
    moved = min(share, held.get(giver, 0.0))
    if moved <= EPSILON or giver == receiver:
        return 0.0
    held[giver] -= moved
    if held[giver] <= EPSILON:
        del held[giver]
    held[receiver] = held.get(receiver, 0.0) + moved
    rows = getattr(record, "tenancies", {}).get(tile, [])
    for row in rows:
        if row["tenant"] == receiver and row["lessor"] == giver:
            row["share"] -= min(row["share"], moved)
    record.tenancies[tile] = [row for row in rows if row["share"] > EPSILON] if rows else rows
    if not record.tenancies.get(tile):
        record.tenancies.pop(tile, None)
    return moved


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


def settle_tenancies(record, currency: CurrencyId, arable_by_tile: Mapping[TileId, float],
                     management_cost_per_extra_tenancy: float = titles_management.COST_SHARE_PER_EXTRA_TENANCY,
                     land_tax_share_of_rent: float = 0.0,
                     ask_by_tile: Optional[Mapping[TileId, float]] = None) -> List[Transfer]:
    """Each tenant pays its lessor the tile's rent on the share it works, and any arrears, as far as its cash
    goes; the lessor spends the managing cost of its tenancies (titles_management.py) of it on stewards, and
    a tenancy whose cost eats all its rent is given up to the tenant. A tenant more than a year's rent
    behind has left the land: the lessor's title on it goes back to nobody. A lessor whose managing cost and the
    state's land tax (`land_tax_share_of_rent`) together take more than the rent holds a loss, and lets the title
    go. `ask_by_tile` is the rent per hectare a landlord can ask of tenants (land_tenancy.rent_ask), which cuts the
    posted rent where the tenants' outside option is better. Returns the payments."""
    payments: List[Transfer] = []
    if not getattr(record, "tenancies", None):
        return payments
    cash: Dict[AgentId, float] = {}
    counts = titles_management.tenancies_by_lessor(record.tenancies)
    for tile, rows in sorted(record.tenancies.items()):
        posted = record.land_rent.get(tile, 0.0)
        rent = (posted if ask_by_tile is None or tile not in ask_by_tile else min(posted, ask_by_tile[tile])) * arable_by_tile.get(tile, 0.0)
        stewards = min((cohort for cohort in record.cohorts.values() if cohort.tile == tile),
                       key=lambda cohort: (cohort.income_class, cohort.agent_id), default=None)
        kept = []
        for row in rows:
            tenant, lessor = row["tenant"], row["lessor"]
            cost = titles_management.cost_share(counts.get(lessor, 1), management_cost_per_extra_tenancy)
            if cost >= 1.0 - EPSILON:
                pass_title(record, tile, lessor, tenant, row["share"])        # the tenant now holds it outright
                continue
            if cost + land_tax_share_of_rent >= 1.0 - EPSILON:
                release(record, tile, lessor, row["share"])                   # holding it costs more than it earns
                continue
            if tenant not in cash:
                cash[tenant] = max(0.0, record.book.balance(tenant, currency))
            due = rent * row["share"]
            owed = due + row["arrears"]
            paid = min(owed, cash[tenant])
            if paid > 0.0:
                cash[tenant] -= paid
                spent = paid * cost if stewards is not None and stewards.agent_id not in (tenant, lessor) else 0.0
                payments.append(Transfer(tenant, lessor, currency, paid - spent, "tenant_rent"))
                if spent > 0.0:
                    payments.append(Transfer(tenant, stewards.agent_id, currency, spent, "steward_pay"))
            row["arrears"] = owed - paid
            if due > 0.0 and row["arrears"] > due:
                release(record, tile, lessor, row["share"])
            else:
                kept.append(row)
        record.tenancies[tile] = kept
    record.tenancies = {tile: rows for tile, rows in record.tenancies.items() if rows}
    return payments
