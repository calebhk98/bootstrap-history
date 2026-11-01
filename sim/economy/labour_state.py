"""The economy's workforce as the labour core's `MarketState`: people per labour area, trade and ability band.

An area is a tile's labour area key (`labour_area`). Everything the core needs to know about a trade
comes from the setup's trade registry; the unskilled trade is the work anyone can take up at once.
"""
import math
from typing import Dict, Iterable, Mapping, Tuple

from sim.labour.api import MarketState, TradeSpec, opening_labour_market, seed_hours, trade_specs

from . import mint, mint_labour, opening_placement, practice, workforce_version
from .market_memory import market_key
from .setup import area_tile, labour_area


def core_trades(setup, extra_trades: Iterable[str] = ()) -> Dict[str, TradeSpec]:
    """The core's trade specs for the setup's trades, and for any other trade an employer bids for."""
    registry = {trade: {"family": spec.family, "training_years": spec.training_years,
                        "fatality_risk_per_year": spec.fatality_risk_per_year}
                for trade, spec in setup.trades.items()}
    for trade in extra_trades:
        registry.setdefault(trade, {"family": "", "training_years": 0.0})
    registry.setdefault(setup.unskilled_trade, {"family": "", "training_years": 0.0})
    for trade, entry in registry.items():
        entry["fallback"] = trade == setup.unskilled_trade
    return trade_specs(registry)


def plot_trade(setup) -> str:
    """The trade of people working their own land: the trade whose hours the land-only recipes (no bought
    inputs but the tools their workers wear, the ones households grow for themselves, households_own.py) ask
    most of. Empty when none do."""
    hours: Dict[str, float] = {}
    for recipe_id, recipe in setup.recipes.items():
        if any(good not in recipe.tool_wear for good in recipe.inputs) or setup.land_per_run.get(recipe_id, 0.0) <= 0.0:
            continue
        for trade, trade_hours in recipe.labour_hours.items():
            hours[trade] = hours.get(trade, 0.0) + trade_hours
    return max(sorted(hours), key=lambda trade: hours[trade]) if hours else ""


def producers_hours_needed(setup, record) -> Dict[str, Dict[str, float]]:
    """Yearly hours each labour area's producers need of each trade for the runs they expect to sell, and the mint at capacity."""
    hours_needed: Dict[str, Dict[str, float]] = {}
    for producer in record.producers.values():
        recipe = practice.recipe_for(setup.recipes[producer.recipe_id], producer.crew_runs)
        needed = hours_needed.setdefault(labour_area(producer.tile), {})
        for trade, hours in recipe.labour_hours.items():
            needed[trade] = needed.get(trade, 0.0) + producer.expected_sales * hours
    mint_needed = hours_needed.setdefault(labour_area(setup.capital_tile), {})
    for trade, hours in mint_labour.capacity_hours(setup, record.currency, mint.capacity_fine_kilograms(setup, record)).items():
        mint_needed[trade] = mint_needed.get(trade, 0.0) + hours
    return hours_needed


def producers_hours_by_employer(setup, record) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Yearly hours each producer needs of each trade for the runs it expects to sell: area -> trade -> producer."""
    hours: Dict[str, Dict[str, Dict[str, float]]] = {}
    for producer in sorted(record.producers.values(), key=lambda each: each.agent_id):
        for trade, per_run in practice.recipe_for(setup.recipes[producer.recipe_id], producer.crew_runs).labour_hours.items():
            hours.setdefault(labour_area(producer.tile), {}).setdefault(trade, {})[producer.agent_id] = producer.expected_sales * per_run
    return hours


def seeded_hours(setup, hours_needed: Mapping[str, Mapping[str, float]]) -> Dict[str, Dict[str, float]]:
    """Hours each area's work needs of the trades no producer's runs staff, from the society's need shares
    (carriage and the recipes no producer runs yet): the trades the labour core would otherwise hold nobody in."""
    left_out = {plot_trade(setup)}
    return {area: seeds for area, needed in sorted(hours_needed.items())
            for seeds in [seed_hours(setup.need_share_by_trade, needed, setup.trades, left_out)] if seeds}


def opening_workforce(setup, record, hours_per_worker=None) -> MarketState:
    """Each tile's working people placed in the trades its producers need for the runs they expect to sell
    (the opening sized them to final demand) and its mint at capacity, and in the trades the society's need
    holds that no producer runs staff (seeded_hours) and a carriage crew hires; hard trades are staffed from the able,
    the rest work unskilled. A person is counted to sell `hours_per_worker` a year (one figure or one per area; a whole
    working year by default): the hours his household keeps for its plot and its own work are not the market's. The
    trades no hirer asks are not seeded, and their people join the fallback and plot trades. No wage is seeded: the
    first year's clearing sets them."""
    hours_needed = producers_hours_needed(setup, record)
    seeds_by_area = opening_placement.seeds_where_hired(seeded_hours(setup, hours_needed), opening_placement.carriage_trades(setup))
    for area, seeds in seeds_by_area.items():
        hours_needed[area].update(seeds)
    working = {labour_area(tile): people * setup.working_share
               for tile, people in sorted(setup.opening_population_by_tile.items())}
    trades = core_trades(setup, {trade for needed in hours_needed.values() for trade in needed})
    state = opening_labour_market(trades, working, hours_needed, hours_per_worker or setup.working_hours_per_year,
                                  plot_trade(setup) or None)
    return state


def people_by_trade(state: MarketState, area: str) -> Dict[str, float]:
    """Working people in an area, by trade (trainees are not counted)."""
    return {trade: math.fsum(bands) for trade, bands in sorted(state.workers.get(area, {}).items())}


def people_by_trade_everywhere(state: MarketState) -> Dict[str, float]:
    """Working people by trade across every labour area (trainees are not counted)."""
    totals: Dict[str, float] = {}
    for area in sorted(state.workers):
        for trade, people in people_by_trade(state, area).items():
            totals[trade] = totals.get(trade, 0.0) + people
    return dict(sorted(totals.items()))


def scale_people(state: MarketState, area: str, factor: float) -> None:
    """Every worker and trainee in an area, scaled."""
    for bands in state.workers.get(area, {}).values():
        bands[:] = [count * factor for count in bands]
    for cohorts in state.trainees.get(area, {}).values():
        for cohort in cohorts:
            cohort[1] = [count * factor for count in cohort[1]]
    workforce_version.bump(state)


def mirror_wages(wages: Dict[str, float], state: MarketState) -> None:
    """The market wages the core settled, under the economy's market keys, for whoever reads a wage."""
    for area, by_trade in state.wages.items():
        for trade, wage in by_trade.items():
            if wage > 0.0:
                wages[market_key(trade, area)] = wage


def hold_back(state: MarketState, share_by_area: Mapping[str, float]) -> Tuple[MarketState, Dict[str, Dict[str, list]]]:
    """The state the market sees when households keep hours back for their own plots: each area's
    workers cut by the share held (the same share of every trade and band), and the people held. The
    given state is cut in place and handed back; the caller replaces it with the year's result."""
    seen = state
    held: Dict[str, Dict[str, list]] = {}
    for area, share in share_by_area.items():
        if share <= 0.0:
            continue
        for trade, bands in seen.workers.get(area, {}).items():
            held.setdefault(area, {})[trade] = [count * share for count in bands]
            bands[:] = [count * (1.0 - share) for count in bands]
    workforce_version.bump(seen)
    return seen, held


def give_back(state: MarketState, held: Mapping[str, Mapping[str, list]]) -> None:
    """The held people rejoin their trades after the year's moves."""
    for area, by_trade in held.items():
        workers = state.workers.setdefault(area, {})
        for trade, bands in by_trade.items():
            now = workers.setdefault(trade, [0.0] * len(bands))
            now[:] = [count + back for count, back in zip(now, bands)]
    workforce_version.bump(state)
