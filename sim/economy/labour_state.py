"""The economy's workforce as the labour core's `MarketState`: people per labour area, trade and ability band.

An area is a tile's labour area key (`labour_area`). Everything the core needs to know about a trade
comes from the setup's trade registry; the unskilled trade is the work anyone can take up at once.
"""
import math
from collections.abc import Mapping as MappingBase
from typing import Dict, Iterable, Mapping, Sequence

import numpy

from sim.labour.api import (MarketState, TradeSpec, grid_rows_of, opening_labour_market, people_at, people_by_trade_in_each_area, people_by_trade_over, people_in_areas, scale_people_in_area, scale_people_in_areas, seed_hours, trade_specs,
                            wages_in_view_order, working_people_in_areas)

from . import households_own, mint, mint_labour, opening_hours_needed, opening_placement, practice
from .market_memory import market_key, note_written
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
        if not households_own.is_own_plot_recipe(recipe_id, recipe, setup.land_per_run):
            continue
        for trade, trade_hours in recipe.labour_hours.items():
            hours[trade] = hours.get(trade, 0.0) + trade_hours
    return max(sorted(hours), key=lambda trade: hours[trade]) if hours else ""


def producers_hours_needed(setup, record) -> Dict[str, Dict[str, float]]:
    """Yearly hours each labour area's producers need of each trade for the runs they expect to sell, and the mint at capacity."""
    hours_needed = opening_hours_needed.of_producers(
        [(practice.recipe_for(setup.recipes[producer.recipe_id], producer.crew_runs), labour_area(producer.tile),
          producer.expected_sales) for producer in record.producers.values()])
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


def opening_workforce(setup, record, hours_per_worker=None, carriage_hours=None) -> MarketState:
    """Each tile's working people placed in the trades its producers need for the runs they expect to sell
    (the opening sized them to final demand) and its mint at capacity, and in the trades the society's need
    holds that no producer runs staff (seeded_hours) and a carriage crew hires, to the hours `carriage_hours` ({area: {trade: hours}}) gives the crews; hard trades are staffed from the able,
    the rest work unskilled. A person is counted to sell `hours_per_worker` a year (one figure or one per area; a whole
    working year by default): the hours his household keeps for its plot and its own work are not the market's. The
    trades no hirer asks are not seeded, and their people join the fallback and plot trades. No wage is seeded: the
    first year's clearing sets them."""
    hours_needed = producers_hours_needed(setup, record)
    seeds_by_area = opening_placement.seeds_where_hired(seeded_hours(setup, hours_needed), carriage_hours or {})
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
    return people_by_trade_over(state, [area])


def people_in_pairs(state: MarketState, areas: Iterable[str], trades: Iterable[str]) -> numpy.ndarray:
    """Working people of each (area, trade) pair given as two lists of equal length; zero for a pair the state holds no entry for."""
    return people_at(state, grid_rows_of(state, areas, trades))


def people_by_trade_matrix(state: MarketState, areas: Iterable[str]):
    """Working people of the areas as (people per area and trade, the trade names in name order): zero where an area has no entry."""
    totals, _seen = people_by_trade_in_each_area(state, areas)
    return totals, state.ids.trades.names


class PeopleByTile(MappingBase):
    """Working people by tile and trade over every labour area of the state. The first read takes every tile's figures in one block
    (`people_by_trade_in_each_area`); a tile's trades are made into a dict, and kept, when it is read."""

    def __init__(self, state: MarketState):
        self._state = state
        names = state.ids.areas.names
        self._area_of_tile = {area_tile(area): area for area in sorted(names[number] for number in state.named_areas("workers"))}
        self._read: Dict[str, Dict[str, float]] = {}
        self._place = {tile: place for place, tile in enumerate(self._area_of_tile)}
        self._block = None

    def __getitem__(self, tile):
        if tile not in self._read:
            place = self._place[tile]
            if self._block is None:
                self._block = people_by_trade_in_each_area(self._state, self._area_of_tile.values())
            totals, seen = self._block
            names = self._state.ids.trades.names
            self._read[tile] = {names[trade]: float(totals[place, trade]) for trade in numpy.flatnonzero(seen[place]).tolist()}
        return self._read[tile]

    def working_people(self, tiles) -> float:
        """Everyone working on the tiles: `math.fsum` over the tiles of each tile's trades' people (a tile with no workers adds nothing)."""
        areas = [self._area_of_tile[tile] for tile in tiles if tile in self._area_of_tile]
        return math.fsum(working_people_in_areas(self._state, areas).tolist())

    def __iter__(self):
        return iter(self._area_of_tile)

    def __len__(self):
        return len(self._area_of_tile)


def people_by_trade_everywhere(state: MarketState) -> Dict[str, float]:
    """Working people by trade across every labour area (trainees are not counted)."""
    return people_by_trade_over(state, sorted(state.workers))


def working_people_of_areas(state: MarketState, areas: Iterable[str]) -> numpy.ndarray:
    """Everyone working in each area (`math.fsum` of its trades' people), zero for an area the state holds nobody in."""
    return working_people_in_areas(state, areas)


def follow_working_people(state: MarketState, areas: Sequence[str], people: numpy.ndarray, unskilled_trade: str, add_workers) -> None:
    """The core's people (workers and trainees) in each area brought to the working `people` the cohorts hold there: an area the core
    holds nobody in gets them in the unskilled trade (`add_workers(area, trade, people)`), any other is scaled by one factor."""
    held = people_in_areas(state, areas)
    for place in numpy.flatnonzero(held <= 0.0).tolist():
        add_workers(areas[place], unskilled_trade, float(people[place]))
    scaled = numpy.flatnonzero((held > 0.0) & (held != people))
    scale_people_in_areas(state, [areas[place] for place in scaled.tolist()], people[scaled] / held[scaled])


def scale_people(state: MarketState, area: str, factor: float) -> None:
    """Every worker and trainee in an area, scaled."""
    scale_people_in_area(state, area, factor)


def mirror_wages(wages: Dict[str, float], state: MarketState) -> None:
    """Rebuild whole the remembered wages from the core's wages (`state.wages`, area -> trade -> wage) under the economy's
    market keys, for whoever reads a wage: a market the core holds no wage for is not quoted one. The only writer of
    `MarketMemory.wages`; the opening calls it with the seeds in a state of their own."""
    wages.clear()
    note_written()
    areas, trades, found = wages_in_view_order(state, 0.0)
    keys = [market_key(trade, area) for area, trade in zip(areas, trades)]
    if hasattr(wages, "admit_keys"):
        wages.admit_keys(keys)      # numbered in sorted order, whatever order the core named its wages in
    if hasattr(wages, "set_many"):
        wages.set_many(keys, found.tolist())
        return
    for key, wage in zip(keys, found.tolist()):
        wages[key] = wage
