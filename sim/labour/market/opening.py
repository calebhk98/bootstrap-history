"""A starting labour market: each area's working people placed in the trades its work needs.

The hardest trades are staffed first, each band giving people in proportion to its share of those who
could finish the trade (aptitude.completion_chance), so a hard trade's people come from the able bands
and the easy trades take who is left. The fallback trade takes the people its own work needs; the rest,
whom no employer needs, work their own plots as the idle trade when one is named, else join the fallback.
Trainees start empty and wages start unset; a few `year.run_year`s from here settle them.
"""
from typing import Dict, Mapping, Optional

from . import aptitude
from .records import MarketState, TradeSpec
from .trades import fallback_trade


def opening_state(trades: Mapping[str, TradeSpec], working_people_by_area: Mapping[str, float],
                  hours_needed: Mapping[str, Mapping[str, float]], hours_per_worker_year: float,
                  idle_trade: Optional[str] = None) -> MarketState:
    """`hours_needed[area][trade]` is the yearly hours that area's work asks of each trade. `idle_trade` is the
    trade of people no employer needs (the households working their own land)."""
    fallback = fallback_trade(trades)
    state = MarketState()
    for area in sorted(working_people_by_area):
        free = aptitude.split_evenly(max(0.0, working_people_by_area[area]))
        workers: Dict[str, list] = {}
        wanted = hours_needed.get(area, {})
        for trade in sorted((trade for trade in wanted if trade in trades and trade != fallback),
                            key=lambda each: (-trades[each].difficulty, each)):
            people = max(0.0, wanted[trade]) / hours_per_worker_year
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
            needed = max(0.0, wanted.get(fallback, 0.0)) / hours_per_worker_year
            free_total = aptitude.band_total(free)
            kept = min(1.0, needed / free_total) if free_total > 0.0 else 0.0
            idle = [value * (1.0 - kept) for value in free]
            free = [value * kept for value in free]
            workers[idle_trade] = aptitude.add_to(workers.get(idle_trade), idle) if idle_trade in workers else idle
        workers[fallback] = aptitude.add_to(workers.get(fallback), free) if fallback in workers else list(free)
        state.workers[area] = workers
    return state
