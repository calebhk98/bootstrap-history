"""A starting labour market: each area's working people placed in the trades its work needs.

The hardest trades are staffed first, each band giving people in proportion to its share of those who
could finish the trade (aptitude.completion_chance), so a hard trade's people come from the able bands
and the easy trades take who is left. People no trade needs go to the fallback trade. Trainees start
empty and wages start unset; a few `year.run_year`s from here settle them.
"""
from typing import Dict, Mapping

from . import aptitude
from .records import MarketState, TradeSpec
from .trades import fallback_trade


def opening_state(trades: Mapping[str, TradeSpec], working_people_by_area: Mapping[str, float],
                  hours_needed: Mapping[str, Mapping[str, float]], hours_per_worker_year: float) -> MarketState:
    """`hours_needed[area][trade]` is the yearly hours that area's work asks of each trade."""
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
        workers[fallback] = aptitude.add_to(workers.get(fallback), free) if fallback in workers else list(free)
        state.workers[area] = workers
    return state
