"""The hours a newcomer's crew will need, for the entry decision. A new producer starts at the mean practice of the
recipe's other producers (practice.entrant_crew_runs) and learns on the runs it makes (practice.crew_runs_after_year),
so its first years book more hours than the recipe's. Entry weighs the years a producer is judged over before it
exits (LOSS_YEARS_BEFORE_EXIT, producers_close.py): the hours it plans on are the mean of those years' hours, so a
first year that loses and later years that pay enter when the years together pay, as exit would not close them
before then.
"""
import contextlib
import dataclasses
import math
from typing import Callable, Dict, List, Mapping, Sequence

from . import practice
from .producers_close import LOSS_YEARS_BEFORE_EXIT
from .types import Recipe

# recipe id -> the crew_runs of the recipe's existing producers
CrewsOf = Callable[[str], Sequence[Mapping[str, float]]]


_shared: Dict[int, tuple] = {}     # id of a producers table -> (table, its crews_of) while `shared_crews` holds it
_entrants: Dict[tuple, tuple] = {}  # (recipe id, the grouping and recipe of its peers) -> (recipe, peers, their entrant crew_runs) while `shared_crews` is open
_open_blocks = [0]


class _GroupedCrews(list):
    """The crews `shared_crews` hands out for a recipe, carrying which grouping and recipe they are."""
    group: tuple = ()


def crews_of_recipe(producers: Mapping[str, object]) -> CrewsOf:
    """The crews of each recipe's producers in `producers` (a record's producers), in producer id order. Inside
    `shared_crews` of the same table the one grouping is read; otherwise the table is read on each call."""
    held = _shared.get(id(producers))
    if held is not None and held[0] is producers:
        return held[1]

    def crews(recipe_id: str) -> List[Mapping[str, float]]:
        return [each.crew_runs for _name, each in sorted(producers.items()) if each.recipe_id == recipe_id]
    return crews


@contextlib.contextmanager
def shared_crews(producers: Mapping[str, object]):
    """Group `producers` by recipe once, on first use, for every `crews_of_recipe` of the table inside the block. The
    table must not gain, lose or replace a producer inside the block."""
    grouped: Dict[str, List[Mapping[str, float]]] = {}
    state = {"built": False}

    def crews(recipe_id: str) -> List[Mapping[str, float]]:
        if not state["built"]:
            for _name, each in sorted(producers.items()):
                grouped.setdefault(each.recipe_id, []).append(each.crew_runs)
            state["built"] = True
        handed = _GroupedCrews(grouped.get(recipe_id, ()))
        handed.group = (id(grouped), recipe_id)
        return handed
    outer = _shared.get(id(producers))
    _shared[id(producers)] = (producers, crews)
    _open_blocks[0] += 1
    try:
        yield crews
    finally:
        _open_blocks[0] -= 1
        if _open_blocks[0] == 0:
            _entrants.clear()
        if outer is None:
            del _shared[id(producers)]
        else:
            _shared[id(producers)] = outer


def entrant_crew(recipe: Recipe, peers: Sequence[Mapping[str, float]]) -> Dict[str, float]:
    """`practice.entrant_crew_runs`, read once per recipe and peers inside `shared_crews` (the peers' practice cannot
    change there). The caller must not change the returned dict."""
    group = getattr(peers, "group", ())
    if not _open_blocks[0] or not group:
        return practice.entrant_crew_runs(recipe, peers)
    key = (id(recipe), group)
    kept = _entrants.get(key)
    if kept is None or kept[0] is not recipe:
        kept = _entrants[key] = (recipe, list(peers), practice.entrant_crew_runs(recipe, peers))
    return kept[2]


def first_year_recipe(recipe: Recipe, peers: Sequence[Mapping[str, float]]) -> Recipe:
    """The recipe at the hours an entrant's crew needs in its first year."""
    return practice.recipe_for(recipe, entrant_crew(recipe, peers))


_planned: Dict[tuple, tuple] = {}     # (recipe id, planned hours) -> (recipe, the recipe at those hours): one object per recipe and hours
_PLANNED_KEPT = 20000


def planned_recipe(recipe: Recipe, peers: Sequence[Mapping[str, float]], runs_per_year: float,
                   years: int = LOSS_YEARS_BEFORE_EXIT) -> Recipe:
    """The recipe with each trade's hours the mean of an entrant's hours over `years` years of `runs_per_year` runs,
    from the peers' mean practice; the recipe itself when it starts at the floor."""
    crew = entrant_crew(recipe, peers)
    if not crew:
        return recipe
    totals = {trade: [] for trade in recipe.labour_hours}
    for _year in range(max(1, years)):
        hours = practice.recipe_for(recipe, crew).labour_hours
        for trade in totals:
            totals[trade].append(hours[trade])
        crew = practice.crew_runs_after_year(crew, max(0.0, runs_per_year), 0.0, {})
    hours = {trade: math.fsum(each) / len(each) for trade, each in totals.items()}
    key = (id(recipe), tuple(hours.items()))
    kept = _planned.get(key)
    if kept is None or kept[0] is not recipe:
        if len(_planned) > _PLANNED_KEPT:
            _planned.clear()
        kept = _planned[key] = (recipe, dataclasses.replace(recipe, labour_hours=hours))
    return kept[1]
