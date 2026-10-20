"""A version counter on the workforce (the labour core's `MarketState`), and a cache that dies with it.

Every function that writes the workforce calls `bump`; a cached figure is kept with the version it was
summed at and is used only while the version is unchanged, or the workforce object is the same one."""
from typing import Callable, Dict, Hashable

_VERSION = "_workforce_version"
_CACHE = "_workforce_figures"


def version(state) -> int:
    return state.__dict__.get(_VERSION, 0)


def bump(state) -> None:
    """Call after anything writes `state` (its workers, trainees or bands)."""
    state.__dict__[_VERSION] = version(state) + 1
    state.__dict__.pop(_CACHE, None)


def cached(state, key: Hashable, compute: Callable[[], Dict[str, float]]) -> Dict[str, float]:
    """`compute()` for this workforce as it stands, kept until the next `bump`; a copy is handed back."""
    figures = state.__dict__.setdefault(_CACHE, {})
    if key not in figures:
        figures[key] = compute()
    return dict(figures[key])
