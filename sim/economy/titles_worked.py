"""Land a holder works itself: its title less what it has let to tenants, plus what it works as a tenant."""
from typing import Dict, List, Mapping, Sequence

from . import titles
from .types import AgentId, TileId


def worked_share(record, tile: TileId, holder: AgentId) -> float:
    """Share of the tile's land the holder works with its own hands: titles it holds that no tenant works,
    plus the shares it works as a tenant under another holder."""
    return max(0.0, titles.holding(record, tile, holder) - titles.let_out_share(record, tile, holder)) + titles.tenant_share(record, tile, holder)


def worked_shares(record, tiles: Sequence[TileId], holders: Sequence[AgentId]) -> List[float]:
    """`worked_share` of each (tile, holder) pair, the tenancies of a tile read once for all its holders (each sum adds in tenancy order,
    as `titles.let_out_share` and `titles.tenant_share` do)."""
    found: List[float] = []
    by_tile: Dict[TileId, tuple] = {}
    for tile, holder in zip(tiles, holders):
        read = by_tile.get(tile)
        if read is None:
            let_out: Dict[AgentId, list] = {}
            worked: Dict[AgentId, list] = {}
            for row in record.land.tenancies.get(tile, ()):
                let_out.setdefault(row["lessor"], []).append(row["share"])
                worked.setdefault(row["tenant"], []).append(row["share"])
            read = by_tile[tile] = (titles.shares(record, tile), let_out, worked)
        held, let_out, worked = read
        found.append(max(0.0, held.get(holder, 0.0) - sum(let_out.get(holder, ()))) + sum(worked.get(holder, ())))
    return found


def allocate_hectares(asked_by_holder: Mapping[AgentId, float], arable_hectares: float) -> Dict[AgentId, float]:
    """Hectares each holder may work on one tile: what it holds, all cut by one factor if together they
    exceed the tile's arable land."""
    asked = {holder: max(0.0, hectares) for holder, hectares in asked_by_holder.items()}
    total = sum(asked.values())
    scale = min(1.0, max(0.0, arable_hectares) / total) if total > 0.0 else 1.0
    return {holder: hectares * scale for holder, hectares in asked.items()}
