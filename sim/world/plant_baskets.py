"""What a plant physically makes in a year, and what it buys to make it: the baskets of its production entries.

Pure functions of production entries, prices and wages (the baskets half of the kernel, `plant_figures`). Each entry
states per batch what comes out, what is consumed and the hours of work; its plant states the output a year it can
turn out (`annual_output_at_basis`). A line of product is held to the smaller of the plant's capacity and what its
staff's hours make; a declared total output holds all material lines to it (and is the capacity of a line nothing
else bounds). `energy` is any object offering `can_run(entry)`, `bought(carrier, entry)` and `sold(carrier, entry)`:
energy a line draws is priced at the grade its own requirement needs, and energy it makes is sold at the grade its
reach clears. Nothing here reads a node, the engine, or a revenue or upkeep figure.
"""
import math
from collections import defaultdict
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Tuple

from sim.unit_conversions import HOURS_PER_PERSON_YEAR

ENERGY_CARRIERS = ("thermal_mj", "mechanical_mj", "electrical_mj")


def _dominant_output(entry: Mapping[str, Any]) -> str:
    return max(entry["outputs"], key=entry["outputs"].get)


class Baskets(NamedTuple):
    """What a node makes and buys in a year. Energy is kept apart because its price depends on the
    entry: {carrier: {"quantity": megajoules, "value": money}}."""
    outputs: Dict[str, float]
    purchases: Dict[str, float]
    energy_sold: Dict[str, Dict[str, float]]
    energy_bought: Dict[str, Dict[str, float]]
    labour_hours: Dict[str, float]
    plant: List[Tuple[Dict[str, Any], float]]    # each capital good the lines run in, and the share of it they use


def _purchases_per_batch(entry: Mapping[str, Any]) -> Dict[str, float]:
    bought = defaultdict(float)
    for material, quantity in (entry.get("inputs") or {}).items():
        bought[material] += quantity
    return bought


def _energy_bought_per_batch(entry: Mapping[str, Any], energy: Any
                             ) -> Dict[str, Tuple[float, float]]:
    """{carrier: (megajoules, money)} one batch draws, at the price graded to this entry."""
    return {carrier: (entry[carrier], entry[carrier] * energy.bought(carrier, entry))
            for carrier in ENERGY_CARRIERS if entry.get(carrier)}


def _energy_sold_per_batch(entry: Mapping[str, Any], energy: Any
                           ) -> Dict[str, Tuple[float, float]]:
    return {carrier: (quantity, quantity * energy.sold(carrier, entry))
            for carrier, quantity in entry["outputs"].items() if carrier in ENERGY_CARRIERS}


def _plant_units_per_year(entry: Mapping[str, Any]) -> float:
    """Units of the dominant output a year the entry's plant turns out; infinite where no plant is stated."""
    capacities = [capital["annual_output_at_basis"] for capital in entry.get("capital") or []
                  if capital.get("annual_output_at_basis")]
    return min(capacities) if capacities else math.inf


def _hours_per_unit(entry: Mapping[str, Any]) -> float:
    hours = sum((entry.get("labour_hours") or {}).values())
    return hours / entry["outputs"][_dominant_output(entry)]


def net_per_batch(entry: Mapping[str, Any], goods: Mapping[str, float],
                   energy: Any) -> float:
    sold = sum(quantity * goods[material] for material, quantity in entry["outputs"].items()
               if material not in ENERGY_CARRIERS)
    sold += sum(value for _quantity, value in _energy_sold_per_batch(entry, energy).values())
    bought = sum(quantity * goods.get(material, 0.0) for material, quantity in _purchases_per_batch(entry).items())
    bought += sum(value for _quantity, value in _energy_bought_per_batch(entry, energy).values())
    return sold - bought


def _best_entry_per_line(entries: List[Dict[str, Any]], goods: Mapping[str, float],
                         energy: Any) -> List[Dict[str, Any]]:
    """One technique per set of products: the one adding most value for each hour it asks."""
    lines: Dict[frozenset, Dict[str, Any]] = {}
    for entry in entries:
        if not entry.get("outputs") or any(material not in goods for material in entry["outputs"]):
            continue
        if not energy.can_run(entry):
            continue            # needs a grade of heat no technique held supplies
        if entry.get("extracted_from") and not entry.get("capital") and not entry.get("inputs"):
            continue            # gathered from a deposit or a by-product stream: set by that source, not by staff
        key = frozenset(entry["outputs"])
        hours = sum((entry.get("labour_hours") or {}).values()) or 1.0
        score = net_per_batch(entry, goods, energy) / hours
        if key not in lines or score > lines[key][0]:
            lines[key] = (score, entry)
    return [lines[key][1] for key in sorted(lines, key=sorted)]


def _covers_its_staff(entry: Mapping[str, Any], goods: Mapping[str, float], energy: Any,
                      wages: Optional[Mapping[str, float]]) -> bool:
    """True when a batch adds at least what the hours it asks cost at these wages (always, without wages)."""
    if wages is None:
        return True
    staff = sum(wages.get(trade, 0.0) * hours for trade, hours in (entry.get("labour_hours") or {}).items())
    return net_per_batch(entry, goods, energy) >= staff * (1.0 - 1e-9)     # a price at cost adds exactly its staff


def line_capacities(lines: List[Dict[str, Any]], staff_people: float, declared_output_t: float
                    ) -> List[Tuple[Dict[str, Any], float]]:
    """(line, units of its dominant output a year) for each line the plant, the staff or the declared
    output bounds. `staff_people` work a year each; a `declared_output_t` of zero states no total."""
    staff_hours = staff_people * HOURS_PER_PERSON_YEAR
    staffed_lines = [entry for entry in lines if _hours_per_unit(entry) > 0.0] if staff_hours > 0.0 else []
    declared_kilograms = float(declared_output_t or 0.0) * 1000.0
    material_lines = [entry for entry in lines if not any(material in ENERGY_CARRIERS for material in entry["outputs"])]
    units: List[Tuple[Dict[str, Any], float]] = []
    for entry in lines:
        capacity = _plant_units_per_year(entry)
        if entry in staffed_lines:
            capacity = min(capacity, staff_hours / len(staffed_lines) / _hours_per_unit(entry))
        if math.isinf(capacity) and declared_kilograms > 0.0 and entry in material_lines:
            capacity = declared_kilograms / len(material_lines)      # the declared plant is the only bound
        if math.isfinite(capacity) and capacity > 0.0:
            units.append((entry, capacity))
    return units


def yearly_baskets(entries: List[Dict[str, Any]], goods: Mapping[str, float], energy: Any,
                   wages: Optional[Mapping[str, float]], staff_people: float, declared_output_t: float
                   ) -> Optional[Baskets]:
    """The plant's yearly baskets, or None when the data gives it no physical output to derive. A line
    whose batch adds less than its staff cost at `wages` is not run; a plant whose lines are all such
    makes nothing. `entries` are the techniques it may run; `staff_people` and `declared_output_t` bound
    its lines as `line_capacities` says."""
    lines = _best_entry_per_line(entries, goods, energy)
    runnable = [entry for entry in lines if _covers_its_staff(entry, goods, energy, wages)]
    units = line_capacities(runnable, staff_people, declared_output_t)
    if not units:
        return Baskets({}, {}, {}, {}, {}, []) if line_capacities(lines, staff_people, declared_output_t) else None
    declared_kilograms = float(declared_output_t or 0.0) * 1000.0
    material_lines = [entry for entry in runnable if not any(material in ENERGY_CARRIERS for material in entry["outputs"])]
    total_kilograms = sum(units_made for entry, units_made in units if entry in material_lines)
    scale = min(1.0, declared_kilograms / total_kilograms) if declared_kilograms > 0.0 and total_kilograms > 0.0 else 1.0
    outputs: Dict[str, float] = defaultdict(float)
    purchases: Dict[str, float] = defaultdict(float)
    labour: Dict[str, float] = defaultdict(float)
    energy_sold: Dict[str, Dict[str, float]] = defaultdict(lambda: {"quantity": 0.0, "value": 0.0})
    energy_bought: Dict[str, Dict[str, float]] = defaultdict(lambda: {"quantity": 0.0, "value": 0.0})
    for entry, units_made in units:
        line_scale = scale if entry in material_lines else 1.0
        batches = units_made * line_scale / entry["outputs"][_dominant_output(entry)]
        for material, quantity in entry["outputs"].items():
            if material not in ENERGY_CARRIERS:
                outputs[material] += quantity * batches
        for material, quantity in _purchases_per_batch(entry).items():
            purchases[material] += quantity * batches
        for trade, hours in (entry.get("labour_hours") or {}).items():
            labour[trade] += hours * batches
        for basket, per_batch in ((energy_sold, _energy_sold_per_batch(entry, energy)),
                                  (energy_bought, _energy_bought_per_batch(entry, energy))):
            for carrier, (quantity, value) in per_batch.items():
                basket[carrier]["quantity"] += quantity * batches
                basket[carrier]["value"] += value * batches
    plant: Dict[str, Tuple[Dict[str, Any], float]] = {}
    for entry, units_made in units:
        for capital in entry.get("capital") or []:
            basis = capital.get("annual_output_at_basis")
            used = min(1.0, units_made * (scale if entry in material_lines else 1.0) / basis) if basis else 1.0
            plant[capital["good"]] = (capital, max(used, plant.get(capital["good"], (capital, 0.0))[1]))
    return Baskets(dict(outputs), dict(purchases), {key: dict(value) for key, value in energy_sold.items()},
                   {key: dict(value) for key, value in energy_bought.items()}, dict(labour), list(plant.values()))
