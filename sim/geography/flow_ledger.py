"""A ledger of the goods carried between places in a year, and what it says about the carriers' return trips.

A carrier that goes out loaded and comes back empty charges the loaded leg for the whole round trip
(`freight_cost.return_leg_factor`). When goods also flow the other way over the same pair of places,
the opposite flow fills part of the return, so the haul is cheaper by that share. The ledger holds
tonnes by (origin, destination); the rest reads the one-sidedness of each pair off it.

Standalone: plain dicts ({origin: {destination: tonnes}}) in and out, so the owner saves it as it is.
"""
from typing import Dict, Mapping

from . import freight_cost

Ledger = Dict[str, Dict[str, float]]


def record_flow(ledger: Ledger, origin: str, destination: str, tonnes: float) -> None:
    """Add `tonnes` carried from one place to another (nothing for a stay or a negative amount)."""
    if origin == destination or tonnes <= 0.0:
        return
    row = ledger.setdefault(origin, {})
    row[destination] = row.get(destination, 0.0) + tonnes


def tonnes_between(ledger: Mapping[str, Mapping[str, float]], origin: str, destination: str) -> float:
    return float(ledger.get(origin, {}).get(destination, 0.0))


def pair_imbalance(ledger: Mapping[str, Mapping[str, float]], origin: str, destination: str) -> float:
    """How one-sided the trade over a pair of places was, in [0, 1]: 1 when nothing came back (or
    nothing is known), 0 when the tonnes each way match."""
    return freight_cost.imbalance_of_flows(
        tonnes_between(ledger, origin, destination), tonnes_between(ledger, destination, origin))


def return_fill_share(ledger: Mapping[str, Mapping[str, float]], origin: str, destination: str) -> float:
    """Share of the carrier's capacity the opposite flow fills on the way back, 0 to 1."""
    out = tonnes_between(ledger, origin, destination)
    back = tonnes_between(ledger, destination, origin)
    return 0.0 if out <= 0.0 else min(1.0, back / out)


def overall_imbalance(ledger: Mapping[str, Mapping[str, float]]) -> float:
    """The tonne-weighted one-sidedness over every pair of places: the share of the year's tonnes that
    found no opposite flow to fill the return. 1 for an empty ledger (carriers return empty, the
    default when nothing is known). TRANSITIONAL HEURISTIC: each pair is a corridor of its own, so a
    cart that serves several pairs on one trip is not given the chance to fill its return from them."""
    one_sided = 0.0
    total = 0.0
    for origin, row in ledger.items():
        for destination, tonnes in row.items():
            if origin < destination:
                back = tonnes_between(ledger, destination, origin)
                one_sided += abs(tonnes - back)
                total += tonnes + back
            elif tonnes_between(ledger, destination, origin) <= 0.0:
                one_sided += tonnes
                total += tonnes
    return 1.0 if total <= 0.0 else one_sided / total
