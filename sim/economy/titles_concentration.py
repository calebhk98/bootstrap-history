"""How concentrated land titles are: the hectares each holder holds, summarised as the top decile's share
and a Gini over holders. A validation read (CLAUDE.md 4.2), never an input to the model."""
from typing import Dict, Mapping, Sequence

from . import titles
from .types import AgentId, TileId


def hectares_by_holder(tiles: Mapping[TileId, object], record) -> Dict[AgentId, float]:
    """Hectares of cropland each holder holds through its titles; every cohort is a holder, with zero if it holds none."""
    held: Dict[AgentId, float] = {cohort_id: 0.0 for cohort_id in record.cohorts}
    for tile_id, tile in sorted(tiles.items()):
        for holder, share in titles.shares(record, tile_id).items():
            held[holder] = held.get(holder, 0.0) + share * tile.cropland_hectares
    return held


def top_decile_share(holdings: Sequence[float]) -> float:
    """Share of all land held by the richest tenth of holders (at least one holder)."""
    ordered = sorted(holdings)
    total = sum(ordered)
    if total <= 0.0:
        return 0.0
    top_count = max(1, round(0.1 * len(ordered)))
    return sum(ordered[-top_count:]) / total


def gini(holdings: Sequence[float]) -> float:
    ordered = sorted(holdings)
    count, total = len(ordered), sum(ordered)
    if count == 0 or total <= 0.0:
        return 0.0
    return sum((2 * (rank + 1) - count - 1) * amount for rank, amount in enumerate(ordered)) / (count * total)


def summary(tiles: Mapping[TileId, object], record) -> Dict[str, float]:
    holdings = list(hectares_by_holder(tiles, record).values())
    return {"holders": float(len(holdings)), "top_decile_share": top_decile_share(holdings), "gini": gini(holdings)}
