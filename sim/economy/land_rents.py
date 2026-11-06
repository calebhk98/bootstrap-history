"""Rent paid on land, read back from the economy's records: what the land market let land at last year, per tile."""
from typing import Dict, Iterable, Mapping

from . import titles
from .types import AgentId, TileId, Transfer


def rent_paid_by_tile(record) -> Dict[TileId, float]:
    """Money (in the economy's units) producers paid in rent on each tile last year, as the land market booked it
    (`booked_by_tile`). A tile where no rent was paid is absent."""
    return dict(sorted(record.land.rent_paid.items()))


def booked_by_tile(postings: Iterable[Transfer], producers: Mapping[AgentId, object]) -> Dict[TileId, float]:
    """The rent postings of producers summed by the producer's tile; a posting from an agent that is not a producer is left out."""
    paid: Dict[TileId, float] = {}
    for posting in postings:
        producer = producers.get(posting.payer)
        if producer is not None and posting.amount > 0.0:
            paid[producer.tile] = paid.get(producer.tile, 0.0) + posting.amount
    return dict(sorted(paid.items()))


def rent_received_by_cohort(record, tiles=None) -> Dict[str, float]:
    """Rent each title holder received last year: the rent paid on a tile is shared among the tile's title holders by
    their shares, as `ownership.spread` pays it. Only the tiles in `tiles` when given. A holder that is not a household
    cohort (the state, a firm) is in the result too."""
    received: Dict[str, float] = {}
    for tile, paid in rent_paid_by_tile(record).items():
        if tiles is not None and tile not in tiles:
            continue
        for holder, amount in titles.split_among_holders(record, tile, paid).items():
            received[holder] = received.get(holder, 0.0) + amount
    return received
