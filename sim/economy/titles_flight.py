"""Land a fleeing tenant leaves: the share he worked goes out of his tenancy and the lessor's title on it goes back to
no holder, the same ending `titles.settle_tenancies` gives a tenant who falls too far behind."""
from typing import Dict, List

from .titles import EPSILON, release


def tenant_flees(record, tenant: str, fleeing_share: float) -> Dict[str, float]:
    """`fleeing_share` (0..1) of everything `tenant` works leaves the land. Each tenancy of his shrinks by that share
    and the lessor's title on the share he left is released (538). Returns the share released per tile."""
    fleeing_share = max(0.0, min(1.0, fleeing_share))
    released: Dict[str, float] = {}
    if fleeing_share <= 0.0:
        return released
    for tile in sorted(getattr(record, "tenancies", {})):
        kept: List[dict] = []
        for row in record.tenancies[tile]:
            if row["tenant"] == tenant:
                left = row["share"] * fleeing_share
                release(record, tile, row["lessor"], left)
                released[tile] = released.get(tile, 0.0) + left
                row["share"] -= left
            if row["share"] > EPSILON:
                kept.append(row)
        record.tenancies[tile] = kept
    record.tenancies = {tile: rows for tile, rows in record.tenancies.items() if rows}
    return released
