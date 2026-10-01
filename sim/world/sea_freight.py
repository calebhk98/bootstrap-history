"""Sea freight: a wind-driven merchant hull's physical inputs per tonne-km.

The wind does the work, so there is no feed term for animals: what a tonne-km
costs is the crew's hours and rations spread over the cargo and the ground
the hull covers in a day. Same output shape as `sim/world/transport.py`
(`FreightPhysicalInputs`), so a route can pick the cheapest mode without
caring which one it is. No prices here: the caller turns rations and hours
into money.

Standalone: nothing from `sim/engine/`.
"""
from sim.constants import declare
from sim.unit_conversions import METERS_PER_KILOMETER

from .transport import FreightPhysicalInputs

SECONDS_PER_HOUR = 3600.0
HOURS_PER_DAY = 24.0

MERCHANT_HULL_CARGO_TONNES = declare(
    "MERCHANT_HULL_CARGO_TONNES", 120.0, kind="engineering_estimate",
    unit="tonnes of cargo per hull",
    source="Wreck and textual evidence for ancient Mediterranean and Indian "
           "Ocean merchantmen (Casson, Ships and Seamanship in the Ancient "
           "World): the common hull carried on the order of a hundred "
           "tonnes; the great grain ships several times that.",
    confidence="C",
    why="Cargo one hull lifts per voyage; more cargo spreads the crew over "
        "more tonnes.")

MERCHANT_HULL_CREW = declare(
    "MERCHANT_HULL_CREW", 12.0, kind="engineering_estimate",
    unit="crew per hull",
    source="Casson, Ships and Seamanship in the Ancient World: a hull of "
           "about a hundred tonnes sailed with a master, a mate and a "
           "dozen or so hands.",
    confidence="C",
    why="People who must be fed and paid for every day the hull is at sea.")

CREW_HOURS_AT_SEA_PER_DAY = declare(
    "CREW_HOURS_AT_SEA_PER_DAY", 24.0, kind="engineering_estimate",
    unit="paid crew-hours per crew member per day at sea",
    source="A hull sails night and day on watches; a hand is engaged for "
           "the whole day however the watches rotate.",
    confidence="C",
    why="Hours of crew attention billed per day the hull covers ground.")

AVERAGE_VOYAGE_SPEED_KNOTS = declare(
    "AVERAGE_VOYAGE_SPEED_KNOTS", 2.5, kind="engineering_estimate",
    unit="knots made good over a whole voyage",
    source="Casson and Pryor on sailing-ship passage times: a square-rigged "
           "hull makes good two to three knots over a full voyage once "
           "head winds, calms and harbour waits are counted, though it runs "
           "faster in a fair wind.",
    confidence="C",
    why="Ground covered per day sets how far the crew's day is spread.")

KILOMETRES_PER_NAUTICAL_MILE = declare(
    "KILOMETRES_PER_NAUTICAL_MILE", 1.852, kind="physical_constant",
    unit="km per nautical mile", source="Definition.", confidence="A",
    why="Converts knots to km per hour.")

CREW_RATION_KG_OF_GRAIN_PER_DAY = declare(
    "CREW_RATION_KG_OF_GRAIN_PER_DAY", 1.0, kind="biological_parameter",
    unit="kg of grain per person per day",
    source="An adult needs roughly three thousand kilocalories a day for "
           "heavy work; a kilogram of grain gives about three and a half "
           "thousand.",
    confidence="B",
    why="Food the crew eats each day at sea, priced as grain by the caller.")

SAILING_DAYS_PER_YEAR = declare(
    "SAILING_DAYS_PER_YEAR", 150.0, kind="engineering_estimate",
    unit="days at sea per year", source="Sailing seasons: ancient shipping "
    "largely stopped in winter.", confidence="C",
    why="With the hull's working life, sets the distance it covers before "
        "it is worn out.")

HULL_SERVICE_LIFE_YEARS = declare(
    "HULL_SERVICE_LIFE_YEARS", 25.0, kind="engineering_estimate",
    unit="years", source="Typical working life of a wooden merchant hull "
    "with lead sheathing and repairs.", confidence="C",
    why="Hull wear per tonne-km is the hull's whole life spread over the "
        "tonne-km it carries.")

HULL_TIMBER_KG_PER_CARGO_TONNE = declare(
    "HULL_TIMBER_KG_PER_CARGO_TONNE", 800.0, kind="engineering_estimate",
    unit="kg of timber per tonne of cargo capacity",
    source="A wooden merchantman's hull, mast and rigging weighed close to its cargo; "
           "Casson gives hulls of this class a lightship weight of the order of the cargo.",
    confidence="D",
    why="Sets the hull's price (timber at its price) for the carrier's capital charge.")

PORT_HANDLING_HOURS_PER_TONNE = declare(
    "PORT_HANDLING_HOURS_PER_TONNE", 2.0, kind="temporary_heuristic",
    unit="labour-hours per tonne per sea leg (loading plus unloading)",
    source=None, confidence="D",
    why="Stevedoring at the two ports of a sea leg; a person shifts "
        "roughly a tonne in a few hours with ropes and baskets. Not yet "
        "derived from a lifting model.")


def ground_km_per_day():
    return AVERAGE_VOYAGE_SPEED_KNOTS * KILOMETRES_PER_NAUTICAL_MILE * HOURS_PER_DAY


def sailing_freight_physical_inputs(cargo_tonnes=None, crew=None):
    """Physical inputs per tonne-km for a merchant hull under sail."""
    cargo_tonnes = MERCHANT_HULL_CARGO_TONNES if cargo_tonnes is None else cargo_tonnes
    crew = MERCHANT_HULL_CREW if crew is None else crew
    if cargo_tonnes <= 0.0 or crew <= 0.0:
        raise ValueError("a hull needs cargo space and a crew")
    distance_per_day_km = ground_km_per_day()
    tonne_km_per_day = cargo_tonnes * distance_per_day_km
    feed_kg_per_day = crew * CREW_RATION_KG_OF_GRAIN_PER_DAY
    service_life_km = HULL_SERVICE_LIFE_YEARS * SAILING_DAYS_PER_YEAR * distance_per_day_km
    return FreightPhysicalInputs(
        mode="sailing merchant hull, %d crew, %d t" % (crew, cargo_tonnes),
        cargo_tonnes=cargo_tonnes, distance_per_day_km=distance_per_day_km,
        tonne_km_per_day=tonne_km_per_day, feed_kg_per_day=feed_kg_per_day,
        feed_kg_per_tonne_km=feed_kg_per_day / tonne_km_per_day,
        driver_hours_per_tonne_km=crew * CREW_HOURS_AT_SEA_PER_DAY / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=1.0 / (service_life_km * cargo_tonnes))
