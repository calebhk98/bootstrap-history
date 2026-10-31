"""A small economy built by hand, for scenario tests of `sim.economy` without the engine.

Three tiles in a row: a coastal town, a farm tile, and a tile where ore is worked. Goods: a grain
that feeds people, an ore dug by miners, and a metal smelted from it that is also the money's backing
and an ornament. The builders (`small_setup()`, `stationary_setup()`) live in sim/economy/fixture_setups.py
and are re-exported here; `run(setup, years)` opens an `Economy` and steps it, returning the economy and
each year's outcome. Nothing is read from data/, so a test states every figure it depends on.
"""
import contextlib
import dataclasses
from unittest import mock

from sim.economy import opening_income
from sim.economy.economy import Economy
from sim.economy.fixture_setups import (
    FARM, FARMS, FOOD, GRAIN, HILLS, LABOURER, METAL, MINE, MINER, ORE, ORNAMENT, PLOT_LAND_PER_RUN, SMELT, SMITH,
    TOWN, basket, recipes, small_setup, specs, stationary_setup, tiles)
from sim.economy.protocols import YearInputs
from sim.economy.setup import EconomySetup
from sim.economy.tile_costs import world_map_of
from sim.economy.types import TileSpec

def quiet_year(setup: EconomySetup, **changes) -> YearInputs:
    """A year with the opening's people and no engine orders."""
    inputs = YearInputs(year=0, population_by_tile={}, working_age_share=setup.working_share,
                        yield_factor_by_producer={}, engine_orders={})
    return dataclasses.replace(inputs, **changes) if changes else inputs


def run(setup: EconomySetup = None, years: int = 5, inputs_for_year=None):
    """Open the economy and step it `years` times. `inputs_for_year(economy, year)` may supply each
    year's inputs; otherwise every year is quiet. Returns (economy, outcomes)."""
    setup = setup or small_setup()
    economy = Economy(setup)
    outcomes = []
    for year in range(years):
        inputs = inputs_for_year(economy, year) if inputs_for_year else quiet_year(setup)
        outcomes.append(economy.step(inputs))
    return economy, outcomes



NORTH_PORT, NORTH_FARMS = "north_port", "north_farms"
NORTH = "north"


def two_country_setup(**changes) -> EconomySetup:
    """The three-tile economy and a second country on two tiles to its north, which can grow grain but has no
    miners or smiths (its techniques allow only the farm recipe)."""
    base = small_setup()
    the_tiles = dict(base.tiles)
    the_tiles[FARMS] = dataclasses.replace(the_tiles[FARMS], borders=the_tiles[FARMS].borders + (NORTH_FARMS,))
    the_tiles[NORTH_FARMS] = TileSpec(NORTH_FARMS, 40.0, 9.5, 2000.0, False, (FARMS, NORTH_PORT), 0.6, 1.0, country=NORTH)
    the_tiles[NORTH_PORT] = TileSpec(NORTH_PORT, 40.0, 9.0, 1000.0, True, (NORTH_FARMS,), 0.3, 1.0, country=NORTH)
    people = dict(base.opening_population_by_tile)
    people.update({NORTH_FARMS: 2500.0, NORTH_PORT: 1500.0})
    setup = dataclasses.replace(
        base, tiles=the_tiles, world_map=world_map_of(the_tiles), opening_population_by_tile=people,
        recipes_by_country={base.civ_id: tuple(sorted(base.recipes)), NORTH: (FARM,)})
    return dataclasses.replace(setup, **changes) if changes else setup


@contextlib.contextmanager
def surplus_households():
    """Within the block, open economies with households' income at the full-employment ceiling (split by what each
    class owns) instead of the income the opening's demand pays (opening_income.py). That income leaves a household
    its floors and no surplus, because it is the income at which a household with a propensity to spend below one
    spends no more than it is paid. A test about what a household does with a surplus (ornaments, durables, imports
    it can afford, a new drink) or about something that does not depend on how well off it is (where producers sit)
    states that it wants one."""
    with mock.patch.object(opening_income, "settled_income_per_head",
                           lambda ceiling, _people, _demand_at: (ceiling, 0.0)):
        yield


def households_with_a_surplus(test_case):
    """`surplus_households` for the length of `test_case`."""
    patch = mock.patch.object(opening_income, "settled_income_per_head",
                              lambda ceiling, _people, _demand_at: (ceiling, 0.0))
    patch.start()
    test_case.addCleanup(patch.stop)
