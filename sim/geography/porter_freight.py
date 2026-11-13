"""Porters on foot as a freight carrier: the physical inputs per tonne-km, from a foot mode's `carrier` data.

The same arithmetic as the route search's porter rate (`routes_rates._porter`): a load per person, a day's
walk, a day's hours. A porter's own ration is the wage's (the labour market pays it), so the carrier has no
feed to price; the ration rides on the porter and takes lift from the cargo. Prices are the caller's.

Standalone: `transport` and `provisions` of this package.
"""
from typing import Any, Mapping

from sim.geography import transport
from sim.unit_conversions import KILOGRAMS_PER_TONNE


def freight_physical_inputs(carrier: Mapping[str, Any]) -> "transport.FreightPhysicalInputs":
    """Physical inputs per tonne-km of one porter: {load_kg, km_per_day, work_hours_per_day, ration_kg_per_day}."""
    cargo_tonnes = float(carrier["load_kg"]) / KILOGRAMS_PER_TONNE
    km_per_day = float(carrier["km_per_day"])
    tonne_km_per_day = cargo_tonnes * km_per_day
    return transport.FreightPhysicalInputs(
        mode="porter carrying %d kg" % carrier["load_kg"], cargo_tonnes=cargo_tonnes,
        distance_per_day_km=km_per_day, tonne_km_per_day=tonne_km_per_day, feed_kg_per_day=0.0,
        feed_kg_per_tonne_km=0.0, driver_hours_per_tonne_km=float(carrier["work_hours_per_day"]) / tonne_km_per_day,
        vehicle_wear_fraction_per_tonne_km=0.0, carried_kg_per_day=float(carrier["ration_kg_per_day"]))
