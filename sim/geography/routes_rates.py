"""What one tonne-km costs a mode on one edge, in physical inputs: pace, crew hours, feed and fuel.

Each mode's `model` (map data) picks the physics: pack, draught and barge reuse `transport.py`,
sailing reuses `sea_freight.py`; porter, rail, steamship and fixed are computed from the mode's
`carrier` inputs. Pace falls with grade as 1 / (1 + (grade / critical_grade)^2) (a labelled shape);
per-day costs (crew, feed) rise as pace falls, fuel burnt per km does not. A mode that cannot work
at the grade, or against the current, has no rate. Money is the caller's: see `physical_cost` for
the scalar used when no prices are supplied.

Standalone: `transport`, `sea_freight` and the map's parameters.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sim.geography import parameters, sea_freight, transport
from sim.geography.map_source import MapDataError, WorldMap

KILOGRAMS_PER_TONNE = 1000.0
JOULES_PER_MEGAJOULE = 1.0e6
GRADE_STEP = 0.002
CURRENT_STEP_KM_PER_HOUR = 0.1


@dataclass(frozen=True)
class Rate:
    """Per tonne-km on one edge: ground pace and the physical inputs used."""
    km_per_day: float
    labour_hours: float
    feed_kg: float = 0.0
    fuel_kg: float = 0.0


def physical_cost(world_map: WorldMap, rate: Rate) -> float:
    """Labour-hours per tonne-km with feed and fuel converted at the map's labour-hours per kg."""
    return (rate.labour_hours
            + rate.feed_kg * parameters.parameter(world_map, "route_feed_labour_hours_per_kg")
            + rate.fuel_kg * parameters.parameter(world_map, "route_fuel_labour_hours_per_kg"))


def _named(name: str) -> Any:
    found = getattr(transport, str(name).upper(), None)
    if found is None:
        raise MapDataError("route mode names %r, which sim/geography/transport.py does not define" % name)
    return found


def _from_freight_inputs(inputs, pace: float) -> Rate:
    return Rate(inputs.distance_per_day_km * pace, inputs.driver_hours_per_tonne_km / pace,
                inputs.feed_kg_per_tonne_km / pace)


def _porter(carrier: Dict[str, Any], pace: float) -> Rate:
    porters_per_tonne = KILOGRAMS_PER_TONNE / carrier["load_kg"]
    km_per_day = carrier["km_per_day"] * pace
    return Rate(km_per_day, porters_per_tonne * carrier["work_hours_per_day"] / km_per_day,
                porters_per_tonne * carrier["ration_kg_per_day"] / km_per_day)


def _rail(carrier: Dict[str, Any], grade: float, pace: float) -> Rate:
    resistance = carrier["rolling_resistance"] + grade
    joules_per_tonne_km = (KILOGRAMS_PER_TONNE * transport.GRAVITATIONAL_ACCELERATION_M_PER_S2
                           * resistance * KILOGRAMS_PER_TONNE)
    fuel_joules_per_kg = carrier["fuel_mj_per_kg"] * JOULES_PER_MEGAJOULE
    km_per_day = carrier["km_per_day"] * pace
    return Rate(km_per_day,
                carrier["crew"] * carrier["crew_hours_per_day"] / (carrier["train_tonnes"] * km_per_day),
                0.0, joules_per_tonne_km / (carrier["thermal_efficiency"] * fuel_joules_per_kg))


def _steamship(carrier: Dict[str, Any], pace: float, current_km_per_hour: float) -> Optional[Rate]:
    water_km_per_day = carrier["km_per_day"] * pace
    ground = water_km_per_day + current_km_per_hour * sea_freight.HOURS_PER_DAY
    if ground <= 0.0:
        return None
    return Rate(ground, carrier["crew"] * carrier["crew_hours_per_day"] / (carrier["cargo_tonnes"] * ground),
                0.0, carrier["fuel_kg_per_tonne_km"] * water_km_per_day / ground)


def compute_rate(world_map: WorldMap, mode: Dict[str, Any], edge_class: str, grade: float,
                 current_km_per_hour: float) -> Optional[Rate]:
    """The mode's rate on an edge of this class, grade and current (positive: with the current)."""
    if grade > mode.get("max_grade", 1.0):
        return None
    pace = 1.0 / (1.0 + (grade / mode.get("critical_grade", 1.0)) ** 2)
    pace *= mode.get("class_pace_factor", {}).get(edge_class, 1.0)
    if mode.get("pace_factor_parameter"):
        pace *= parameters.parameter(world_map, mode["pace_factor_parameter"])
    model, carrier = mode["model"], mode.get("carrier", {})
    try:
        if model == "porter":
            return _porter(carrier, pace)
        if model == "pack":
            return _from_freight_inputs(transport.pack_freight_physical_inputs(
                _named(carrier["animal"]), carrier["string_size"], grade_fraction=grade), pace)
        if model == "draught":
            return _from_freight_inputs(transport.draught_freight_physical_inputs(
                _named(carrier["animal"]), carrier["team_size"], _named(carrier["vehicle"]),
                _named(carrier["surface"]), grade), pace)
        if model == "barge":
            return _from_freight_inputs(transport.barge_freight_physical_inputs(
                _named(carrier["animal"]), carrier["team_size"], _named(carrier["vehicle"]),
                current_km_per_hour=current_km_per_hour), pace)
        if model == "sailing":
            return _from_freight_inputs(sea_freight.sailing_freight_physical_inputs(), pace)
        if model == "rail":
            return _rail(carrier, grade, pace)
        if model == "steamship":
            return _steamship(carrier, pace, current_km_per_hour)
        if model == "fixed":
            return Rate(carrier["km_per_day"] * pace, carrier.get("labour_hours_per_tonne_km", 0.0) / pace,
                        carrier.get("feed_kg_per_tonne_km", 0.0) / pace, carrier.get("fuel_kg_per_tonne_km", 0.0))
    except ValueError:
        return None  # the carrier cannot move cargo at this grade or against this current
    raise MapDataError("route mode %r has unknown model %r" % (mode.get("id"), model))


class RateTable:
    """Rates by (mode, edge class, grade step, current step), computed once each."""

    def __init__(self, world_map: WorldMap, modes: Dict[str, Dict[str, Any]]):
        self.world_map = world_map
        self.modes = modes
        self._rates: Dict[Tuple[str, str, int, int], Optional[Rate]] = {}

    def rate(self, mode_id: str, edge_class: str, grade: float, current_km_per_hour: float = 0.0) -> Optional[Rate]:
        grade_step = round(grade / GRADE_STEP)
        current_step = round(current_km_per_hour / CURRENT_STEP_KM_PER_HOUR)
        key = (mode_id, edge_class, grade_step, current_step)
        if key not in self._rates:
            self._rates[key] = compute_rate(self.world_map, self.modes[mode_id], edge_class,
                                            grade_step * GRADE_STEP, current_step * CURRENT_STEP_KM_PER_HOUR)
        return self._rates[key]


def rate_table(world_map: WorldMap) -> RateTable:
    """The map's rate table, kept on the map."""
    table = world_map.__dict__.get("_route_rates")
    if table is None:
        table = RateTable(world_map, world_map.catalogue("route_modes"))
        world_map.__dict__["_route_rates"] = table
    return table
