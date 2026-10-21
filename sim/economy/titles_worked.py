"""Land a holder works itself: its title less what it has let to tenants, plus what it works as a tenant."""
from typing import Dict, Mapping

from . import titles
from .types import AgentId, TileId


def worked_share(record, tile: TileId, holder: AgentId) -> float:
    """Share of the tile's land the holder works with its own hands: titles it holds that no tenant works,
    plus the shares it works as a tenant under another holder."""
    return max(0.0, titles.holding(record, tile, holder) - titles.let_out_share(record, tile, holder)) + titles.tenant_share(record, tile, holder)


def allocate_hectares(asked_by_holder: Mapping[AgentId, float], arable_hectares: float) -> Dict[AgentId, float]:
    """Hectares each holder may work on one tile: what it holds, all cut by one factor if together they
    exceed the tile's arable land."""
    asked = {holder: max(0.0, hectares) for holder, hectares in asked_by_holder.items()}
    total = sum(asked.values())
    scale = min(1.0, max(0.0, arable_hectares) / total) if total > 0.0 else 1.0
    return {holder: hectares * scale for holder, hectares in asked.items()}
