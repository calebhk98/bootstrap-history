"""Directed-hours overhead: functions a mod or another model registers to charge hours against the directed-hours pool.

Each is `function(sim) -> hours a year already spoken for` (management layers, a civil service, a guild's meetings).
The labour package counts the total as committed hours, so every free-hours check sees it. With none registered the
total is zero and nothing changes.
"""
from typing import Callable, List

OVERHEADS: List[Callable] = []


def register(function: Callable) -> Callable:
    if function not in OVERHEADS:
        OVERHEADS.append(function)
    return function


def total_hours(sim) -> float:
    """Sum of every registered overhead; a negative answer counts as zero."""
    return sum(max(0.0, float(function(sim))) for function in OVERHEADS)
