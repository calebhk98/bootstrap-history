"""A starting labour market: each area's working people placed in the trades its work needs.

The hardest trades are staffed first, each band giving people in proportion to its share of those who
could finish the trade (aptitude.completion_chance), so a hard trade's people come from the able bands
and the easy trades take who is left. The fallback trade takes the people its own work needs; the rest,
whom no employer needs, work their own plots as the idle trade when one is named, else join the fallback.
Trainees start empty and wages start unset; a few `year.run_year`s from here settle them.
"""
from typing import Dict, Mapping, Optional, Union

from . import aptitude
from .records import MarketState, TradeSpec
from .trades import fallback_trade


def hours_a_person_sells(area: str, hours_per_worker_year: Union[float, Mapping[str, float]]) -> float:
    """The hours a person of `area` sells: the area's figure in a mapping (the mapping's largest where it names none), or the one figure."""
    if not isinstance(hours_per_worker_year, Mapping):
        return hours_per_worker_year
    return hours_per_worker_year.get(area) or max(hours_per_worker_year.values(), default=1.0)


def opening_state(trades: Mapping[str, TradeSpec], working_people_by_area: Mapping[str, float],
                  hours_needed: Mapping[str, Mapping[str, float]],
                  hours_per_worker_year: Union[float, Mapping[str, float]],
                  idle_trade: Optional[str] = None) -> MarketState:
    """`hours_needed[area][trade]` is the yearly hours that area's work asks of each trade. `idle_trade` is the
    trade of people no employer needs (the households working their own land). `hours_per_worker_year` is the hours a
    person sells a year, one figure or one per area: people are placed as hours wanted over the hours a person of
    their area sells."""
    fallback = fallback_trade(trades)
    state = MarketState()
    for area in sorted(working_people_by_area):
        free = aptitude.split_evenly(max(0.0, working_people_by_area[area]))
        workers: Dict[str, list] = {}
        wanted = hours_needed.get(area, {})
        hours_per_worker = hours_a_person_sells(area, hours_per_worker_year)
        for trade in sorted((trade for trade in wanted if trade in trades and trade != fallback),
                            key=lambda each: (-trades[each].difficulty, each)):
            people = max(0.0, wanted[trade]) / hours_per_worker
            able = [count * chance for count, chance in zip(free, aptitude.completion_by_band(trades[trade].difficulty))]
            able_total = aptitude.band_total(able)
            if people <= 0.0 or able_total <= 0.0:
                continue
            share = min(1.0, people / able_total)
            taken = [value * share for value in able]
            for index, value in enumerate(taken):
                free[index] -= value
            workers[trade] = taken
        if idle_trade in trades and idle_trade != fallback:
            needed = max(0.0, wanted.get(fallback, 0.0)) / hours_per_worker
            free_total = aptitude.band_total(free)
            kept = min(1.0, needed / free_total) if free_total > 0.0 else 0.0
            idle = [value * (1.0 - kept) for value in free]
            free = [value * kept for value in free]
            workers[idle_trade] = aptitude.add_to(workers.get(idle_trade), idle) if idle_trade in workers else idle
        workers[fallback] = aptitude.add_to(workers.get(fallback), free) if fallback in workers else list(free)
        state.workers[area] = workers
    return state
