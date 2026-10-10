"""A steam train as a freight carrier: the physical inputs per tonne-km, from the mode's carrier data.

The same physics as the route search's rail rate (`routes_rates._rail`): the energy to overcome rolling
resistance on level track, drawn from fuel at the engine's thermal efficiency, a crew working the day,
and the pace. On top of it the carrier's capital: the rolling stock (locomotive and wagons, a mass per
tonne of cargo) wearing out over a service life in kilometres. Prices are the caller's.

Standalone: `transport` and `provisions` of this package.
"""
from typing import Any, Dict, Mapping

from sim.geography import provisions, routes_rates, transport
from sim.unit_conversions import KILOGRAMS_PER_TONNE


def freight_physical_inputs(carrier: Mapping[str, Any]) -> "transport.FreightPhysicalInputs":
    """Physical inputs per tonne-km for a train described by a rail mode's `carrier` data, on level track:
    fuel is the feed, the crew's hours are the driver hours, the stock's wear is the vehicle wear."""
    cargo_tonnes = float(carrier["train_tonnes"])
    km_per_day = float(carrier["km_per_day"])
    rate = routes_rates.compute_rate(None, {"model": "rail", "carrier": dict(carrier)}, "land", 0.0, 0.0)
    tonne_km_per_day = cargo_tonnes * km_per_day
    fuel_kg_per_day = rate.fuel_kg * tonne_km_per_day
    return transport.FreightPhysicalInputs(
        mode="steam train, %d crew, %d t" % (carrier["crew"], cargo_tonnes),
        cargo_tonnes=cargo_tonnes, distance_per_day_km=km_per_day, tonne_km_per_day=tonne_km_per_day,
        feed_kg_per_day=fuel_kg_per_day, feed_kg_per_tonne_km=rate.fuel_kg,
        driver_hours_per_tonne_km=rate.labour_hours,
        vehicle_wear_fraction_per_tonne_km=1.0 / (float(carrier["stock_service_life_km"]) * cargo_tonnes),
        carried_kg_per_day=fuel_kg_per_day + provisions.person_provisions_kg_per_day(carrier["crew"]))


def carrier_record(carrier: Mapping[str, Any]) -> Dict[str, Any]:
    """{inputs, fuel_material, stock_material, stock_kg}: the freight inputs and what the caller must price,
    the fuel burnt and the rolling stock (its mass in kilograms)."""
    return {"inputs": freight_physical_inputs(carrier), "fuel_material": carrier["fuel_material"],
            "stock_material": carrier["stock_material"],
            "stock_kg": float(carrier["train_tonnes"]) * float(carrier["stock_tonnes_per_cargo_tonne"]) * KILOGRAMS_PER_TONNE}
