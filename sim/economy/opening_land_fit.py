"""The opening holds each producer to the land it was granted.

The land market clears a tile's ground among the producers' asks and the households' plots (opening_rent.settle) and
states the runs a producer's grant allows where that is less than it asked. The first year's plan works no more than
that, so a producer sized for more opens with sales it cannot make, and the users of what it makes with inputs that
are not there. Here its sales and plant are cut to the grant, and the users of what only land makes are held to what
is left (opening_runs.fit_to_supply)."""
from typing import Optional, Tuple

from . import opening_runs, producer_table


def held_to_land(expected_sales: float, capacity_runs: float, land_run_cap: Optional[float]) -> Tuple[float, float]:
    """(expected sales, capacity) of a producer held to the runs its granted land allows, the plant cut by the same
    share; unchanged where the land is no limit."""
    if land_run_cap is None or expected_sales <= 0.0 or land_run_cap >= expected_sales:
        return expected_sales, capacity_runs
    share = max(0.0, land_run_cap) / expected_sales
    return expected_sales * share, capacity_runs * share


def fit_to_land(setup, record) -> None:
    """Every producer is held to its land (`held_to_land`), then the users of what only land makes to that supply."""
    for producer_id, producer in sorted(record.producers.items()):
        sales, capacity = held_to_land(producer.expected_sales, producer.capacity_runs, producer.land_run_cap)
        if sales != producer.expected_sales:
            producer_table.set_fields(record.producers, producer_id, capacity_runs=capacity, expected_sales=sales)
    opening_runs.fit_to_supply(setup, record, setup.land_per_run)
