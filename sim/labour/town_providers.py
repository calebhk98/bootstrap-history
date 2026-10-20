"""Town-size providers: functions a mod or another model registers to say how many people live in a tile's town.

The labour package's own estimate (labour_settlement.py) is a nominal size scaled by the tile's place in the nation.
A provider is `function(labour, tile, nominal_people) -> people or None`; None means no opinion. When several
are registered the last one in name order that answers wins. The answer is still bounded by the tile's people.
"""
from typing import Callable, Dict, Optional

PROVIDERS: Dict[str, Callable] = {}


def register_town_provider(name: str, function: Callable) -> None:
    """Register `function` under `name`; registering a name again replaces it."""
    PROVIDERS[name] = function


def provided_town_population(labour, tile: str, nominal_people: float) -> Optional[float]:
    answer = None
    for name in sorted(PROVIDERS):
        found = PROVIDERS[name](labour, tile, nominal_people)
        if found is not None:
            answer = max(0.0, float(found))
    return answer
