"""Rent paid on land, read back from the economy's records: what the land market let land at last year, per tile."""
from typing import Dict

from . import titles
from .types import TileId


def rent_paid_by_tile(setup, record) -> Dict[TileId, float]:
    """Money (in the economy's units) producers paid in rent on each tile: each producer's rent a run times the runs it
    worked last year. A tile where no land was let is absent."""
    paid: Dict[TileId, float] = {}
    for producer in record.producers.values():
        rent = producer.land_rent_per_run * max(0.0, producer.last_runs)
        if setup.land_per_run.get(producer.recipe_id, 0.0) > 0.0 and rent > 0.0:
            paid[producer.tile] = paid.get(producer.tile, 0.0) + rent
    return paid


def rent_received_by_cohort(setup, record, tiles=None) -> Dict[str, float]:
    """Rent each title holder received last year: the rent paid on a tile is shared among the tile's title holders by
    their shares, as `ownership.spread` pays it. Only the tiles in `tiles` when given. A holder that is not a household
    cohort (the state, a firm) is in the result too."""
    received: Dict[str, float] = {}
    for tile, paid in rent_paid_by_tile(setup, record).items():
        if tiles is not None and tile not in tiles:
            continue
        for holder, amount in titles.split_among_holders(record, tile, paid).items():
            received[holder] = received.get(holder, 0.0) + amount
    return received
