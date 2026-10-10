"""Live animals walked to market: the cargo is the carrier.

A herd driven overland needs no cart and no pack saddle. It costs what the animals eat on the road
and the drovers' days, and it loses some of the herd to weight and straying each day. Nothing here
is priced: the physical inputs per tonne-km come out as for the other carriers, and the daily loss
rate is mode data (`cargo_loss_per_day`) which the cargo's cost share counts.

Standalone: `transport` and `provisions` of this package.
"""
from typing import Any, Mapping

from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE, METERS_PER_KILOMETER

from . import provisions, transport

DROVING_WALKING_RESISTANCE = declare(
    "DROVING_WALKING_RESISTANCE", 0.03, kind="temporary_heuristic",
    unit="force on level ground as a fraction of the animal's weight", source=None, confidence="D",
    why="An animal walking unladen does work against its own legs' friction and its body's rise and "
        "fall, which the feed has to cover on top of maintenance. A small share of body weight is "
        "the order of the cost of transport of a walking cow or ox; not fitted to a measurement.")


def freight_physical_inputs(carrier: Mapping[str, Any]) -> "transport.FreightPhysicalInputs":
    """Physical inputs per tonne-km of a herd driven by a mode's `carrier` data: {animal, head_per_drover,
    km_per_day, drover_hours_per_day}. Feed is what the herd eats in a day (maintenance and the work of
    walking) over the tonnes it weighs and the km it covers; the drovers' hours likewise; no vehicle."""
    animal = getattr(transport, str(carrier["animal"]).upper())
    head = float(carrier["head_per_drover"])
    km_per_day = min(float(carrier["km_per_day"]), transport.distance_per_day_km(animal))
    herd_tonnes = head * animal.body_mass_kg / KILOGRAMS_PER_TONNE
    walking_joules = (head * animal.body_mass_kg * transport.GRAVITATIONAL_ACCELERATION_M_PER_S2
                      * DROVING_WALKING_RESISTANCE * km_per_day * METERS_PER_KILOMETER)
    feed_kg = transport._feed_kg_from_work_and_maintenance(  # pylint: disable=protected-access
        head * transport.maintenance_kcal_per_day(animal), walking_joules)
    tonne_km_per_day = herd_tonnes * km_per_day
    return transport.FreightPhysicalInputs(
        mode="%d %s walked by one drover" % (head, animal.name), cargo_tonnes=herd_tonnes,
        distance_per_day_km=km_per_day, tonne_km_per_day=tonne_km_per_day, feed_kg_per_day=feed_kg,
        feed_kg_per_tonne_km=feed_kg / tonne_km_per_day,
        driver_hours_per_tonne_km=float(carrier["drover_hours_per_day"]) / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=0.0,
        carried_kg_per_day=provisions.person_provisions_kg_per_day(1))
