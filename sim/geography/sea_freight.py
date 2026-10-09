"""Sea freight: a wind-driven merchant hull's physical inputs per tonne-km.

The wind does the work, so there is no feed term for animals: what a tonne-km
costs is the crew's hours and rations spread over the cargo and the ground
the hull covers in a day. Same output shape as `sim/geography/transport.py`
(`FreightPhysicalInputs`), so a route can pick the cheapest mode without
caring which one it is. No prices here: the caller turns rations and hours
into money.

Standalone: nothing from `sim/engine/`.
"""
import math

from sim.constants import declare
from sim.unit_conversions import METERS_PER_KILOMETER

from .provisions import person_provisions_kg_per_day, PERSON_GRAIN_RATION_KG_PER_DAY
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

SAIL_AREA_M2_PER_CARGO_TONNE_TWO_THIRDS = declare(
    "SAIL_AREA_M2_PER_CARGO_TONNE_TWO_THIRDS", 10.0, kind="engineering_estimate",
    unit="m2 of sail per (tonne of cargo) to the two thirds",
    source="Sail area scales with a hull's cross-section, so with its displacement to the two "
           "thirds; Casson, Ships and Seamanship in the Ancient World, gives a square sail of "
           "a couple of hundred square metres for a hull of about a hundred tonnes.",
    confidence="D",
    why="Sets the sail a hull must work, and so the hands it needs.")

SAIL_AREA_ONE_HAND_WORKS_M2 = declare(
    "SAIL_AREA_ONE_HAND_WORKS_M2", 50.0, kind="engineering_estimate",
    unit="m2 of sail per hand on a watch",
    source="A hand hauls braces and halyards against the wind's load on the sail; square sails "
           "of a couple of hundred square metres were worked by a handful of hands (Casson).",
    confidence="D",
    why="Hands on watch to trim the sail: the rig's area over what one hand can work.")

HELMSMEN_PER_WATCH = declare(
    "HELMSMEN_PER_WATCH", 1, kind="engineering_estimate",
    unit="hands at the steering oars per watch",
    source="One hand holds the steering oar or tiller at a time.", confidence="C",
    why="A hull under way is steered every hour, besides its sail being worked.")

WATCH_HOURS_PER_HAND_PER_DAY = declare(
    "WATCH_HOURS_PER_HAND_PER_DAY", 12.0, kind="biological_parameter",
    unit="hours on watch per hand per day",
    source="A hand sleeps, eats and rests for about half the day; a hull sails night and day, so "
           "the day is split into watches no longer than a hand can keep.",
    confidence="C",
    why="Watches needed to keep a hull under way all day: a day over a hand's hours.")

PIRATE_BOARDING_PARTY = declare(
    "PIRATE_BOARDING_PARTY", 20.0, kind="temporary_heuristic",
    unit="people in a boarding party", source=None, confidence="D",
    why="Raiders who meet a merchant hull come in a boat carrying a few dozen; the number is "
        "not derived from a model of piracy. Robbery succeeds with the share of the two sides' "
        "strength that is the raiders' (strength as the square of numbers, Lanchester's law of "
        "aimed fire at close range), so a lone sailor is easy to rob and a large crew is not.")

PIRATE_ENCOUNTERS_PER_THOUSAND_KM = declare(
    "PIRATE_ENCOUNTERS_PER_THOUSAND_KM", 0.004, kind="temporary_heuristic",
    unit="meetings with raiders per 1000 km sailed", source=None, confidence="D",
    why="How often a hull meets a boarding party; not derived from coasts, trade density and "
        "naval policing, which no model supplies yet.")

SEA_WRECK_PER_THOUSAND_KM = declare(
    "SEA_WRECK_PER_THOUSAND_KM", 0.002, kind="temporary_heuristic",
    unit="share of hulls lost to weather and rocks per 1000 km sailed", source=None,
    confidence="D",
    why="Storms and groundings take a share of hulls on every voyage; not derived from a weather "
        "and coast model.")

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


def crew_to_sail(cargo_tonnes):
    """Hands a hull of this cargo needs to sail night and day: the helm and the hands to trim a sail
    scaled to the hull, on each watch, with as many watches as a hand's hours leave. Never one."""
    sail_area = SAIL_AREA_M2_PER_CARGO_TONNE_TWO_THIRDS * max(0.0, cargo_tonnes) ** (2.0 / 3.0)
    hands_per_watch = HELMSMEN_PER_WATCH + max(1, math.ceil(sail_area / SAIL_AREA_ONE_HAND_WORKS_M2))
    watches = max(2, math.ceil(HOURS_PER_DAY / WATCH_HOURS_PER_HAND_PER_DAY))
    return watches * hands_per_watch


def boarding_loss_share(crew):
    """Share of meetings with a boarding party that end with the hull taken: the raiders' strength
    over the sum of both sides', strength the square of numbers."""
    raiders = PIRATE_BOARDING_PARTY ** 2
    return raiders / (raiders + max(0.0, crew) ** 2)


def hull_loss_per_thousand_km(crew=None):
    """Share of hulls lost per 1000 km sailed: weather, and boarding parties met on the way that
    take a hull with this crew (the default hull's own crew when none is given)."""
    crew = crew_to_sail(MERCHANT_HULL_CARGO_TONNES) if crew is None else crew
    return SEA_WRECK_PER_THOUSAND_KM + PIRATE_ENCOUNTERS_PER_THOUSAND_KM * boarding_loss_share(crew)


def defenders_to_hire(rig_crew, defender_cost_per_day, value_at_risk):
    """Hands to sign on beyond the rig's need: the number that least sums their keep and the expected
    loss of the hull and cargo (`value_at_risk`) over 1000 km sailed, since a larger crew is taken less
    often. The rig's crew is the floor; the search stops where a crew far larger than the raiders'
    party no longer lowers the loss."""
    days_per_thousand_km = 1000.0 / ground_km_per_day()
    cheapest, fewest = math.inf, 0
    for defenders in range(int(4 * PIRATE_BOARDING_PARTY) + 1):
        cost = (defenders * defender_cost_per_day * days_per_thousand_km
                + max(0.0, value_at_risk) * hull_loss_per_thousand_km(rig_crew + defenders))
        if cost < cheapest:
            cheapest, fewest = cost, defenders
    return fewest


def sailing_freight_physical_inputs(cargo_tonnes=None, crew=None):
    """Physical inputs per tonne-km for a merchant hull under sail, crewed for its rig unless a crew
    is given."""
    cargo_tonnes = MERCHANT_HULL_CARGO_TONNES if cargo_tonnes is None else cargo_tonnes
    crew = crew_to_sail(cargo_tonnes) if crew is None else crew
    if cargo_tonnes <= 0.0 or crew <= 0.0:
        raise ValueError("a hull needs cargo space and a crew")
    distance_per_day_km = ground_km_per_day()
    tonne_km_per_day = cargo_tonnes * distance_per_day_km
    feed_kg_per_day = crew * PERSON_GRAIN_RATION_KG_PER_DAY
    service_life_km = HULL_SERVICE_LIFE_YEARS * SAILING_DAYS_PER_YEAR * distance_per_day_km
    return FreightPhysicalInputs(
        mode="sailing merchant hull, %d crew, %d t" % (crew, cargo_tonnes),
        cargo_tonnes=cargo_tonnes, distance_per_day_km=distance_per_day_km,
        tonne_km_per_day=tonne_km_per_day, feed_kg_per_day=feed_kg_per_day,
        feed_kg_per_tonne_km=feed_kg_per_day / tonne_km_per_day,
        driver_hours_per_tonne_km=crew * CREW_HOURS_AT_SEA_PER_DAY / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=1.0 / (service_life_km * cargo_tonnes),
        carried_kg_per_day=person_provisions_kg_per_day(crew))
