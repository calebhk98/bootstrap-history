"""Which techniques a concern can copy from the producers that run them, and when.

A technique one producer runs reaches the other concerns in its line of business only after the time it takes an
actor to copy it (agents/imitation.py `copy_years`), counted from the year it was first seen running; until
then those concerns keep the entries they held. Techniques the society started with are held from the start.
"""
from typing import Any, Dict, FrozenSet, Iterable

from sim.agents.api import imitation

# the opening's techniques were copied before the game began; any copy time is shorter than this
OPENING_SPREAD_YEARS = 10000


def note_first_run(first_run: Dict[str, int], in_use: Iterable[str], year: int, opening: bool) -> None:
    """Record the year each technique in use was first seen. On the `opening` call what is run is the opening's
    and was already spread, so it is stamped long before."""
    stamp = year - OPENING_SPREAD_YEARS if opening else year
    for node_id in sorted(in_use):
        first_run.setdefault(node_id, stamp)


def spread_techniques(in_use: Iterable[str], granted: Iterable[str], first_run: Dict[str, int],
                      nodes: Dict[str, Any], year: int) -> FrozenSet[str]:
    """The techniques in use that the rest of the society has had time to copy by `year`."""
    spread = set(granted)
    for node_id in in_use:
        if node_id in spread:
            continue
        node = nodes.get(node_id)
        if node is None or year - first_run.get(node_id, year) >= imitation.copy_years(node):
            spread.add(node_id)
    return frozenset(spread)
