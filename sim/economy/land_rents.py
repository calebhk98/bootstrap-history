"""Rent paid on land, read back from the economy's records: what the land market let land at last year, per tile."""
from typing import Dict

from .types import TileId


def rent_paid_by_tile(setup, record) -> Dict[TileId, float]:
    """Money (in the economy's units) producers paid in rent on each tile: the tile's rent per hectare times the
    hectare-years its producers worked last year. A tile where no land was let is absent."""
    paid: Dict[TileId, float] = {}
    for producer in record.producers.values():
        hectares = setup.land_per_run.get(producer.recipe_id, 0.0) * max(0.0, producer.last_runs)
        rent = record.land_rent.get(producer.tile, 0.0)
        if hectares > 0.0 and rent > 0.0:
            paid[producer.tile] = paid.get(producer.tile, 0.0) + rent * hectares
    return paid
