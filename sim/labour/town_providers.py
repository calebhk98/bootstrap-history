"""Town-size providers: functions a mod or another model registers to say how many people live in a tile's town.

The labour package's own estimate (labour_settlement.py) is a nominal size scaled by the tile's place in the nation.
A provider is `function(labour, tile, nominal_people) -> people or None`; None means no opinion. When several
are registered the last one in name order that answers wins. The answer is still bounded by the tile's people.

A provider may also give the town's mortality premium: `function(labour, tile, town_people) -> premium or None`, the
excess of the town's baseline death rate over the countryside's as a share of that rate (None: no opinion). The premium
reaches `Population.step` through `SettlementMixin.town_mortality_premium_by_tile`.
"""
from typing import Callable, Dict, Optional

PROVIDERS: Dict[str, Callable] = {}
PREMIUMS: Dict[str, Callable] = {}


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


def register_town_premium(name: str, function: Callable) -> None:
    """Register a mortality-premium function under `name`; registering a name again replaces it."""
    PREMIUMS[name] = function


def provided_mortality_premium(labour, tile: str, town_people: float) -> Optional[float]:
    """The premium the last answering provider gives for the town at `tile` (never negative), or None."""
    answer = None
    for name in sorted(PREMIUMS):
        found = PREMIUMS[name](labour, tile, town_people)
        if found is not None:
            answer = max(0.0, float(found))
    return answer
