"""Conditions and climate envelopes that content data uses to say where something can be.

A condition is {"layer": name, and any of "min", "max", "in", "not_in"}. A tile with no value for
the layer fails the condition unless it says "if_missing": true. An envelope entry is
{"layer": name, "optimal": [low, high], "tolerated": [low, high]}: suitability is 1 inside the
optimal range, falls linearly to 0 at the tolerated bounds, and is 0 outside; an entry with "in"
is 1 or 0. A tile's suitability is the product over entries.
"""
from typing import Any, Callable, Dict, Iterable

from sim.geography.map_source import MapDataError

Lookup = Callable[[str], Any]


def _condition_holds(condition: Dict[str, Any], lookup: Lookup) -> bool:
    found = lookup(condition["layer"])
    if found is None:
        return bool(condition.get("if_missing", False))
    if "in" in condition and found not in condition["in"]:
        return False
    if "not_in" in condition and found in condition["not_in"]:
        return False
    if "min" in condition and float(found) < float(condition["min"]):
        return False
    if "max" in condition and float(found) > float(condition["max"]):
        return False
    return True


def matches(conditions: Iterable[Dict[str, Any]], lookup: Lookup) -> bool:
    """True when every condition holds (an empty list always holds)."""
    return all(_condition_holds(condition, lookup) for condition in conditions)


def _ramp(found: float, optimal, tolerated) -> float:
    optimal_low, optimal_high = float(optimal[0]), float(optimal[1])
    tolerated_low, tolerated_high = float(tolerated[0]), float(tolerated[1])
    if optimal_low <= found <= optimal_high:
        return 1.0
    if found < optimal_low:
        span = optimal_low - tolerated_low
        return 0.0 if span <= 0 or found <= tolerated_low else (found - tolerated_low) / span
    span = tolerated_high - optimal_high
    return 0.0 if span <= 0 or found >= tolerated_high else (tolerated_high - found) / span


def suitability(envelope: Iterable[Dict[str, Any]], lookup: Lookup) -> float:
    """0 to 1: how well a tile suits something with this envelope."""
    total = 1.0
    for entry in envelope:
        found = lookup(entry["layer"])
        if found is None:
            if not entry.get("if_missing", False):
                return 0.0
            continue
        if "in" in entry:
            total *= 1.0 if found in entry["in"] else 0.0
        elif "optimal" in entry:
            tolerated = entry.get("tolerated", entry["optimal"])
            total *= _ramp(float(found), entry["optimal"], tolerated)
        else:
            raise MapDataError("envelope entry for %r needs \"in\" or \"optimal\"" % entry["layer"])
        if total == 0.0:
            return 0.0
    return total
