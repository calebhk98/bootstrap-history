"""Rent paid on land, read back from the economy's records: what the land market let land at last year, per tile."""
from typing import Dict

from .households_cohort import distribute_property_income
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
    """Rent each household cohort received last year: the rent paid on a tile is shared among the tile's
    cohorts by ownership share. Only the tiles in `tiles` when given."""
    received: Dict[str, float] = {}
    for tile, paid in rent_paid_by_tile(setup, record).items():
        if tiles is not None and tile not in tiles:
            continue
        tile_cohorts = [cohort for cohort in record.cohorts.values() if cohort.tile == tile]
        for agent_id, amount in distribute_property_income(tile_cohorts, paid).items():
            received[agent_id] = received.get(agent_id, 0.0) + amount
    return received
