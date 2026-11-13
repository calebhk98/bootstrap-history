"""The physical state of the economy at the end of a year, for judging whether the spin-up settled."""
import math
from typing import Callable, Mapping, Optional

from . import cohort_people


def spin_up_state(setup, record, outcome):
    """Real output and producers' inventories (quantities valued at the opening prices, so a price swing is not
    read as a quantity change), hours hired and idle, unmet need (food floor units short) and, where the record holds
    cohorts, the food need it is measured against (`food_floor_units`)."""
    weight = setup.opening_prices
    held = 0.0
    for agent in record.producers:
        for good, by_tile in record.book.holdings(agent)["goods"].items():
            if good in weight:      # a good with no opening price is left out of the value
                held += weight[good] * sum(by_tile.values())
    return {"real_output": sum(weight[good] * quantity for good, quantity in outcome.output.items() if good in weight),
            "hired_hours": outcome.hired_hours, "idle_hours": outcome.idle_hours, "inventory_value": held,
            "unmet_need": sum(outcome.hunger_by_tile.values()), **_food_need(setup, record)}


def _food_need(setup, record):
    """{"food_need": the food floor units of the record's people}, or nothing for a record with no cohorts."""
    store = getattr(record, "cohorts", None)
    if store is None:
        return {}
    people = cohort_people.total_by_tile(store, "people")
    names = store.names["tiles"].name_list
    return {"food_need": food_floor_units({names[number]: float(count) for number, count in enumerate(people)},
                                          lambda tile: _food_floor_per_person(setup, tile))}


def _food_floor_per_person(setup, tile) -> Optional[float]:
    return next((need.subsistence_per_person for need in setup.basket_for(tile).needs if need.need_id == setup.hunger_need), None)


def food_floor_units(people_by_tile: Mapping[str, float], food_floor_per_person: Callable[[str], Optional[float]]) -> float:
    """The food floor units the economy's people need in a year: each tile's people times its food floor a head."""
    return math.fsum(people * (food_floor_per_person(tile) or 0.0) for tile, people in sorted(people_by_tile.items()) if people > 0.0)
