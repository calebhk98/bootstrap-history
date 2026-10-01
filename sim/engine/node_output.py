"""What a node physically makes in a year, and what it buys to make it.

A node gates production entries (`requires_node`). Each entry states per batch
what comes out, what is consumed and the hours of work; its plant states the
output a year it can turn out (`annual_output_at_basis`). The node's staff
(`sch` + `art` people) supply hours. A line of product is held to the smaller of
the plant's capacity and what the staff's share of hours makes; a node that
declares `annual_output_t` is held to that total as well. Nothing here reads a
revenue figure.
"""
import math
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Tuple

from sim.world.wages import HOURS_PER_WORKER_YEAR

ENERGY_CARRIERS = ("thermal_mj", "mechanical_mj", "electrical_mj")
# TRANSITIONAL (CLAUDE.md 4.4): the goods table prices an energy carrier at one flat pool figure, while an
# entry pays the price graded to its own temperature or kind of work (see `solve_prices_core`), so neither
# energy it buys nor energy it sells is valued here. Needs the solver to expose each entry's graded price.

# (production table, {node id: entries}); the table is kept so a hit is confirmed with `is`
_ENTRIES_BY_NODE: List[Any] = [None, None]


def entries_gated_by(node_id: str, production: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Production entries that become available with this node, in key order."""
    index = _ENTRIES_BY_NODE[1] if _ENTRIES_BY_NODE[0] is production else None
    if index is None:
        index = defaultdict(list)
        for key in sorted(production):
            gate = production[key].get("requires_node")
            if gate:
                index[gate].append(production[key])
        _ENTRIES_BY_NODE[:] = [production, index]
    return index.get(node_id, [])


def _dominant_output(entry: Mapping[str, Any]) -> str:
    return max(entry["outputs"], key=entry["outputs"].get)


def _purchases_per_batch(entry: Mapping[str, Any]) -> Dict[str, float]:
    bought = defaultdict(float)
    for material, quantity in (entry.get("inputs") or {}).items():
        bought[material] += quantity
    return bought


def _plant_units_per_year(entry: Mapping[str, Any]) -> float:
    """Units of the dominant output a year the entry's plant turns out; infinite where no plant is stated."""
    capacities = [capital["annual_output_at_basis"] for capital in entry.get("capital") or []
                  if capital.get("annual_output_at_basis")]
    return min(capacities) if capacities else math.inf


def _hours_per_unit(entry: Mapping[str, Any]) -> float:
    hours = sum((entry.get("labour_hours") or {}).values())
    return hours / entry["outputs"][_dominant_output(entry)]


def _best_entry_per_line(entries: List[Dict[str, Any]], goods: Mapping[str, float]) -> List[Dict[str, Any]]:
    """One technique per set of products: the one adding most value for each hour it asks."""
    lines: Dict[frozenset, Dict[str, Any]] = {}
    for entry in entries:
        if not entry.get("outputs") or any(material not in goods or material in ENERGY_CARRIERS
                                           for material in entry["outputs"]):
            continue
        if entry.get("extracted_from") and not entry.get("capital") and not entry.get("inputs"):
            continue            # gathered from a deposit or a by-product stream: set by that source, not by staff
        key = frozenset(entry["outputs"])
        sold = sum(quantity * goods[material] for material, quantity in entry["outputs"].items())
        bought = sum(quantity * goods.get(material, 0.0)
                     for material, quantity in _purchases_per_batch(entry).items())
        hours = sum((entry.get("labour_hours") or {}).values()) or 1.0
        score = (sold - bought) / hours
        if key not in lines or score > lines[key][0]:
            lines[key] = (score, entry)
    return [lines[key][1] for key in sorted(lines, key=sorted)]


def output_baskets(node: Mapping[str, Any], production: Mapping[str, Any], goods: Mapping[str, float]
                   ) -> Optional[Tuple[Dict[str, float], Dict[str, float]]]:
    """({material: quantity made a year}, {material or energy carrier: quantity bought a year}),
    or None when the data gives the node no physical output to derive."""
    lines = _best_entry_per_line(entries_gated_by(node["id"], production), goods)
    staff_hours = (node.get("sch", 0.0) + node.get("art", 0.0)) * HOURS_PER_WORKER_YEAR
    staffed_lines = [entry for entry in lines if _hours_per_unit(entry) > 0.0] if staff_hours > 0.0 else []
    units: List[Tuple[Dict[str, Any], float]] = []
    for entry in lines:
        capacity = _plant_units_per_year(entry)
        if entry in staffed_lines:
            capacity = min(capacity, staff_hours / len(staffed_lines) / _hours_per_unit(entry))
        if math.isfinite(capacity) and capacity > 0.0:
            units.append((entry, capacity))
    if not units:
        return None
    declared_kilograms = float(node.get("annual_output_t") or 0.0) * 1000.0
    total_kilograms = sum(units_made for _entry, units_made in units)
    scale = min(1.0, declared_kilograms / total_kilograms) if declared_kilograms > 0.0 else 1.0
    outputs: Dict[str, float] = defaultdict(float)
    purchases: Dict[str, float] = defaultdict(float)
    for entry, units_made in units:
        batches = units_made * scale / entry["outputs"][_dominant_output(entry)]
        for material, quantity in entry["outputs"].items():
            outputs[material] += quantity * batches
        for material, quantity in _purchases_per_batch(entry).items():
            purchases[material] += quantity * batches
    return dict(outputs), dict(purchases)
