"""What a carrier eats and drinks on the way, carried as cargo mass.

A crew's food and water, and the feed of the animals that pull or bear the load, ride on the carrier
and take lift from the cargo: the longer the leg between places to restock, the less of the load
arrives as cargo. A leg too long for the carrier to carry what it consumes delivers nothing.

Standalone: physical inputs in, shares out. No prices.
"""
from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE

PERSON_GRAIN_RATION_KG_PER_DAY = declare(
    "PERSON_GRAIN_RATION_KG_PER_DAY", 1.0, kind="biological_parameter",
    unit="kg of grain per person per day",
    source="An adult needs roughly three thousand kilocalories a day for "
           "heavy work; a kilogram of grain gives about three and a half "
           "thousand.",
    confidence="B",
    why="Food a crew member eats each day on the road or at sea, priced as grain by the caller.")

PERSON_WATER_KG_PER_DAY = declare(
    "PERSON_WATER_KG_PER_DAY", 3.0, kind="biological_parameter",
    unit="kg of water per person per day",
    source="Adults working in warm weather drink on the order of three litres a day; a litre of "
           "water weighs a kilogram.",
    confidence="B",
    why="Water a crew member drinks each day, carried because a hull at sea cannot refill it.")


def person_provisions_kg_per_day(people):
    """Mass of the food and water `people` consume in a day."""
    return people * (PERSON_GRAIN_RATION_KG_PER_DAY + PERSON_WATER_KG_PER_DAY)


def delivered_share(inputs, distance_km):
    """Share of a carrier's lift that arrives as cargo over a leg of `distance_km` when it restocks
    only at the leg's ends: the rest is what the crew and animals consume on the way."""
    days = distance_km / inputs.distance_per_day_km
    consumed_kg = inputs.carried_kg_per_day * days
    return max(0.0, 1.0 - consumed_kg / (inputs.cargo_tonnes * KILOGRAMS_PER_TONNE))
