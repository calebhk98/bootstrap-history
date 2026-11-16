"""Reads the figures the opening checks need off an opened game and runs them (opening_checks.py).

`check_civilisation` opens a civilisation's full-length opening (the shipped entries when they match the
source, else computed and kept in the disk cache), takes the spin-up trace for the money check (cached the
same way, and shipped with the openings), steps one year, and returns every check's result.
"""
import os
import random
from typing import Dict, List, Tuple

import sim.geography.api as geography

from sim.knowledge.api import StartDoneYearRecord
from sim.prices.api import solve_cache
from sim.markets import api as markets_api
from sim.markets.api import SPIN_UP_MAXIMUM_YEARS, SPIN_UP_TOLERANCE, SPIN_UP_YEARS_ENV, opening_setup
from . import concern_scan_run, opening_checks
from .data import load, load_civ
from .core import Sim

TRACE_CACHE_DIRECTORY = markets_api.TRACE_CACHE_DIRECTORY


def open_full_length(civ_id: str):
    """A game of `civ_id` on the full-length opening; the environment's shortened spin-up is lifted for it."""
    saved = os.environ.pop(SPIN_UP_YEARS_ENV, None)
    try:
        _tree, _prices, nodes, _wages, _goods = load()
        return Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_id))
    finally:
        if saved is not None:
            os.environ[SPIN_UP_YEARS_ENV] = saved


def trace_key(game) -> str:
    """The cache key of the money trace of `game`'s opening (markets' spin_up_trace_cache)."""
    return markets_api.trace_key_of_setup(opening_setup(game))


def opening_trace(game) -> List[dict]:
    """The spin-up's first stage run for its full length on the opening `game` saved, one row per year; the spin-up
    keeps it when its first stage ran that long, so this is a cache read then."""
    years = int(SPIN_UP_MAXIMUM_YEARS)
    return solve_cache.cached_json(trace_key(game), lambda: markets_api.spin_up_trace(game, years),
                                   cache_dir=TRACE_CACHE_DIRECTORY)


def sited_ores(game) -> List[str]:
    """The ores of the resources the seat has found a deposit of."""
    found = game.view("found_deposits")
    return [ore for resource, ores in geography.ore_goods().items() if found[resource] for ore in ores]


def sited_ore_ratios(ores, prices, costs, stale, kinds, output) -> Tuple[Dict[str, float], Dict[str, str]]:
    """({ore: price over making cost}, {ore: cause}) of the `ores`: those made last year whose price is a trade; every
    other ore is named with its cause (`opening_checks.unmeasured_cause`)."""
    causes = {ore: opening_checks.unmeasured_cause(ore, prices, costs, stale, kinds, output) for ore in ores}
    return ({ore: prices[ore] / costs[ore] for ore, cause in causes.items() if cause is None},
            {ore: cause for ore, cause in causes.items() if cause is not None})


def price_ratios(game) -> Dict[str, Dict[str, Dict[str, object]]]:
    """{group: {"ratios": {good: price over making cost}, "unmeasured": {good: cause}}} for the sited ores, the staple
    and the coin metal, after one step; only goods made last year whose price is a trade (a stale good's shown price is
    its cost, a thin market's is blended toward it). A good left out says why (`opening_checks.unmeasured_cause`)."""
    opened = game.view("agent_opening_figures")()
    prices, costs, stale = game.view("agent_prices")(), game.view("material_prices")(), game.view("agent_stale_goods")()
    kinds, output = game.view("agent_price_kinds")(), game.view("agent_last_outcome")().output
    ratios, unmeasured = sited_ore_ratios(sited_ores(game), prices, costs, stale, kinds, output)
    named = {"staple": game.view("agent_staple")(), "coin_metal": opened["backing_good"]}
    groups = {"sited_ores": {"ratios": ratios, "unmeasured": unmeasured}}
    for group, good in named.items():
        cause = opening_checks.unmeasured_cause(good, prices, costs, stale, kinds, output)
        groups[group] = {"ratios": {good: prices[good] / costs[good]} if cause is None else {},
                         "unmeasured": {} if cause is None else {good or group: cause}}
    return groups


def check_game(game, trace=None) -> List[opening_checks.CheckResult]:
    """Every check on an opened, unplayed game of a full-length opening. It steps the game one year (the
    price and wage figures are the first year's), so the caller passes a game it will not keep playing."""
    result = dict(game.view("agent_spin_up_result")())
    rows = opening_trace(game) if trace is None else trace
    game.send(StartDoneYearRecord())
    game.step()
    outcome = game.view("agent_last_outcome")()
    opened = game.view("agent_opening_figures")()
    ratios = price_ratios(game)
    return [opening_checks.price_over_cost("price_over_cost_" + group, ratios[group]["ratios"], unmeasured=ratios[group]["unmeasured"])
            for group in ("sited_ores", "staple", "coin_metal")] + [
        opening_checks.money_against_wear(rows),
        opening_checks.wage_over_floor(outcome.wages.get(opened["unskilled_trade"]), outcome.wage_floor_per_hour),
        opening_checks.spin_up_settled(result, SPIN_UP_TOLERANCE),
        opening_checks.rate_against_history(opened["opening_rate"], game.view("civilisation")().get("starting_interest_rate"))]


def check_civilisation(civ_id: str) -> List[opening_checks.CheckResult]:
    return check_game(open_full_length(civ_id))


def check_civilisation_and_concerns(civ_id: str, with_checks: bool = True) -> Tuple[List[opening_checks.CheckResult], dict]:
    """(the checks, the concern scan) of `civ_id`'s opening. The scan is taken before the game steps and is reported,
    never a check that can fail (what share should pay is a decision for later); `with_checks=False` skips the
    checks, which step a year and read the money trace."""
    game = open_full_length(civ_id)
    concerns = concern_scan_run.scan_game(game)
    return (check_game(game) if with_checks else []), concerns


def failures(results) -> List[opening_checks.CheckResult]:
    return [each for each in results if not each.passed]


def trace_entry(game) -> Tuple[str, str]:
    """(namespace, key) of the money trace of `game`'s opening, to ship with the opening's other entries."""
    return os.path.basename(TRACE_CACHE_DIRECTORY), trace_key(game)
