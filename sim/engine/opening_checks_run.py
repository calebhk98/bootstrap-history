"""Reads the figures the opening checks need off an opened game and runs them (opening_checks.py).

`check_civilisation` opens a civilisation's full-length opening (the shipped entries when they match the
source, else computed and kept in the disk cache), takes the spin-up trace for the money check (cached the
same way, and shipped with the openings), steps one year, and returns every check's result.
"""
import os
import random
from typing import Dict, List, Tuple

from sim import cache_root
from sim.economy import api as economy_api
from sim.geography import api as geography

from . import economy_port_trace, opening_checks, solve_cache
from .data import load, load_civ
from .economy_port_key import SPIN_UP_SOURCE_MODULES, spin_up_key
from .economy_port_setup import build_setup
from .economy_port_year import SPIN_UP_MAXIMUM_YEARS, SPIN_UP_TOLERANCE, SPIN_UP_YEARS_ENV
from .core import Sim

TRACE_CACHE_DIRECTORY = cache_root.cache_directory("opening_traces")


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
    """The cache key of the money trace of `game`'s opening: that of its spin-up, which covers the data and source."""
    setup = build_setup(game, game.state.economy.agent_economy["opening"])
    return solve_cache.solve_key({"opening_trace": spin_up_key(setup), "years": int(SPIN_UP_MAXIMUM_YEARS)},
                                 source_modules=SPIN_UP_SOURCE_MODULES)


def opening_trace(game) -> List[dict]:
    """The spin-up's first stage run for its full length on the opening `game` saved, one row per year."""
    years = int(SPIN_UP_MAXIMUM_YEARS)
    return solve_cache.cached_json(trace_key(game), lambda: economy_port_trace.spin_up_trace(game, years),
                                   cache_dir=TRACE_CACHE_DIRECTORY)


def sited_ore_ratios(game, prices, costs, stale) -> Dict[str, float]:
    """{ore: price over making cost} of the ores of resources the seat has found a deposit of whose markets cleared lately."""
    return {ore: prices[ore] / costs[ore]
            for resource, ores in geography.ore_goods().items() if game.found_deposits(resource)
            for ore in ores if prices.get(ore) and costs.get(ore) and ore not in stale}


def traded_staple(agent, stale):
    """The good of the hunger need with the largest opening basket quantity among those whose markets cleared
    lately (a good nobody trades shows what it would cost to make, not a price); None when none did."""
    economy = agent.economy()
    setup = economy.setup
    need = next((spec for spec in setup.basket.needs if spec.need_id == setup.hunger_need), None)
    opening = economy_api.opening_quantities(economy)
    goods = [good for good, _effect in need.goods if good not in stale] if need is not None else []
    return max(goods, key=lambda good: opening.get(good, 0.0), default=None)


def price_ratios(game) -> Dict[str, Dict[str, float]]:
    """{group: {good: price over making cost}} for the sited ores, the staple and the coin metal, after one step;
    only goods whose markets cleared lately (a stale good's shown price is its cost, not a trade)."""
    agent = game.economy.agent
    setup = agent.economy().setup
    prices, costs, stale = game.economy.agent_prices(), game._material_prices(), agent.stale_goods()
    named = {"staple": traded_staple(agent, stale), "coin_metal": setup.currency.backing_good}
    ratios = {"sited_ores": sited_ore_ratios(game, prices, costs, stale)}
    for group, good in named.items():
        usable = good and good not in stale and prices.get(good) and costs.get(good)
        ratios[group] = {good: prices[good] / costs[good]} if usable else {}
    return ratios


def check_game(game, trace=None) -> List[opening_checks.CheckResult]:
    """Every check on an opened, unplayed game of a full-length opening. It steps the game one year (the
    price and wage figures are the first year's), so the caller passes a game it will not keep playing."""
    result = dict(game.economy.spin_up_result())
    rows = opening_trace(game) if trace is None else trace
    game.done_year = {}
    game.step()
    outcome = game.economy.agent.outcomes[-1]
    setup = game.economy.agent.economy().setup
    ratios = price_ratios(game)
    return [opening_checks.price_over_cost("price_over_cost_" + group, ratios[group])
            for group in ("sited_ores", "staple", "coin_metal")] + [
        opening_checks.money_against_wear(rows),
        opening_checks.wage_over_floor(outcome.wages.get(setup.unskilled_trade), outcome.wage_floor_per_hour),
        opening_checks.spin_up_settled(result, SPIN_UP_TOLERANCE)]


def check_civilisation(civ_id: str) -> List[opening_checks.CheckResult]:
    return check_game(open_full_length(civ_id))


def failures(results) -> List[opening_checks.CheckResult]:
    return [each for each in results if not each.passed]


def trace_entry(game) -> Tuple[str, str]:
    """(namespace, key) of the money trace of `game`'s opening, to ship with the opening's other entries."""
    return os.path.basename(TRACE_CACHE_DIRECTORY), trace_key(game)
