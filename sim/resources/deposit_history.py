"""The extraction rate each deposit had in the reference civilisation's time, from the older output model.

A deposit carrying a share of the reference empire's output has a rate in tonnes of the resource a year
(`share_of_empire_output` times the empire's output of it, sim/world/deposits.py). That rate, over the
deposit's size, is how fast it was worked, so a deposit worked for millennia is drawn down by the rate it was
worked at and not by a horizon fixed beforehand (sim/geography `mined_before`).
"""
from functools import lru_cache
from typing import Dict

from sim.world import deposits as deposit_model


@lru_cache(maxsize=None)
def _rates(resource_id: str) -> Dict[str, float]:
    return {deposit.name: deposit.quantity_tonnes_per_year for deposit in deposit_model.load_deposits(resource_id)}


def historical_rates(world_map, resource_id: str) -> Dict[str, float]:
    """{deposit id: tonnes of the resource a year} for the deposits the output model rates; empty for a
    resource it does not model."""
    return _rates(resource_id) if resource_id in deposit_model.metals(world_map) else {}
