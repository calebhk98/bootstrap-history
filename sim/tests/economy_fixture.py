"""A small economy built by hand, for scenario tests of `sim.economy` without the engine.

Three tiles in a row: a coastal town, a farm tile, and a tile where ore is worked. Goods: a grain
that feeds people, an ore dug by miners, and a metal smelted from it that is also the money's backing
and an ornament. `small_setup()` returns an `EconomySetup`; `run(setup, years)` opens an `Economy`
and steps it, returning the economy and each year's outcome. Nothing is read from data/, so a test
states every figure it depends on.
"""
import contextlib
import dataclasses
from unittest import mock

from sim.economy import household_hours_year, opening_income, opening_stationary, year_labour
from sim.economy.economy import Economy
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY
from sim.economy.households_basket import Basket, NeedSpec
from sim.economy.protocols import YearInputs
from sim.economy.setup import EconomySetup, TradeSpec
from sim.economy.tile_costs import world_map_of
from sim.economy.types import CurrencySpec, GoodSpec, Recipe, TileSpec

TOWN, FARMS, HILLS = "town", "farms", "hills"
GRAIN, ORE, METAL = "grain_kg", "ore_kg", "metal_kg"
FOOD, ORNAMENT = "food", "ornament"
LABOURER, MINER, SMITH = "labourer", "miner", "smith"
MINE, SMELT, FARM = "dig_ore", "smelt_metal", "grow_grain"


def tiles():
    return {
        TOWN: TileSpec(TOWN, 40.0, 10.0, 1000.0, True, (FARMS,), 0.3, 1.0),
        FARMS: TileSpec(FARMS, 40.0, 10.5, 2000.0, False, (TOWN, HILLS), 0.6, 1.0),
        HILLS: TileSpec(HILLS, 40.0, 11.0, 2000.0, False, (FARMS,), 0.1, 1.0),
    }


def recipes():
    return {
        FARM: Recipe(FARM, {GRAIN: 1000.0}, {}, {LABOURER: 300.0}),
        MINE: Recipe(MINE, {ORE: 1000.0}, {}, {MINER: 40.0}),
        SMELT: Recipe(SMELT, {METAL: 1.0}, {ORE: 1000.0}, {SMITH: 30.0}),
    }


def specs(service_lives=None):
    """The goods; `service_lives` maps a good to the years it lasts (default: used up within the year)."""
    lives = service_lives or {}
    return {
        GRAIN: GoodSpec(GRAIN, 1.0, 0.1, lives.get(GRAIN, 0.0), "food"),
        ORE: GoodSpec(ORE, 1.0, 0.0, lives.get(ORE, 0.0), "ore"),
        METAL: GoodSpec(METAL, 1.0, 0.0, lives.get(METAL, 0.0), "metal"),
    }


def basket():
    needs = (NeedSpec(FOOD, 250.0, 0.6, ((GRAIN, 1.0),)),
             NeedSpec(ORNAMENT, 0.0, 0.05, ((METAL, 1.0),)))
    need_data = {FOOD: {"surplus_budget_share": 0.6}, ORNAMENT: {"surplus_budget_share": 0.05}}
    return Basket(needs, NEED_SUBSTITUTION_ELASTICITY, need_data)


def small_setup(**changes) -> EconomySetup:
    """The three-tile economy; keyword arguments replace any `EconomySetup` field."""
    wages = {LABOURER: 1.0, MINER: 1.2, SMITH: 1.5}
    prices = {GRAIN: 0.3, ORE: 0.05, METAL: 95.0}
    the_tiles = tiles()
    setup = EconomySetup(
        civ_id="fixture",
        currency=CurrencySpec("coin", "struck_coin", METAL, 0.01, "state:fixture", 0.05),
        state_agent="state:fixture", tiles=the_tiles, world_map=world_map_of(the_tiles),
        carriage_rates={"cart": 0.002, "pack": 0.004, "sail": 0.0005},
        handling_rates={"sail": 2.0 * wages[LABOURER]},
        specs=specs(), recipes=recipes(), basket=basket(),
        trades={trade: TradeSpec(trade) for trade in wages},
        tax_forms=(), state_capacity=0.5, working_hours_per_year=2000.0, working_share=0.5,
        gini=0.4, opening_population_by_tile={TOWN: 4000.0, FARMS: 3000.0, HILLS: 1000.0},
        opening_prices=prices, opening_wages=wages, opening_rate=0.06,
        capital_tile=TOWN, port_tile=TOWN)
    return dataclasses.replace(setup, **changes) if changes else setup


PLOT_LAND_PER_RUN = 1.0       # hectare-years a farm run takes, for fixtures whose households grow some of their own grain


def stationary_setup(slack_share: float = 0.0, **changes) -> EconomySetup:
    """The three-tile economy with each worker having the hours its opening's runs hire (plus `slack_share`, none by default: only hours offered equal to hours hired rests), and the
    hours it keeps for its own plot at the stated wage (households_hours_offered.py), not the stated 2000 a year, which
    is many times what the fixture's recipes hire: at those hours the labour market clears at the workers' survival
    wage a dozen times below the stated one, and no year repeats itself. Households work a plot (`land_per_run` on the
    farm recipe), so an hour not sold has a use at home. The runs are those of the stated fixture's opening demand."""
    stated = small_setup(land_per_run={FARM: PLOT_LAND_PER_RUN})
    economy = Economy(stated)
    flows = opening_stationary.solve({TOWN: economy.record.opening_demand}, stated.recipes, stated.opening_prices,
                                     stated.opening_wages, stated.opening_rate)
    workers = sum(stated.opening_population_by_tile.values()) * stated.working_share
    view = economy.view()
    offers = year_labour.labour_offers(stated, economy.record, view, year_labour.outside_option_by_tile(stated, economy.record, view))
    kept = household_hours_year.decide(stated, economy.record, view, offers, economy._own_plot_options(),
                                       economy._hectares_held())
    hours = opening_stationary.hours_that_clear_at(flows.hours_by_trade[LABOURER], workers, slack_share,
                                                   sum(kept.values()) / workers)
    return dataclasses.replace(stated, working_hours_per_year=hours, **changes)


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


@contextlib.contextmanager
def surplus_game_openings():
    """Within the block, a game's agent economy opens with households' income at the full-employment ceiling,
    stated in the setup (so the spin-up cache keeps it apart from the settled opening). See `surplus_households`."""
    from sim.engine import economy_port_year

    def with_ceiling(sim):
        opening = real_opening_values(sim)
        opening["opening_income_per_head"] = float(sim.HOURS_PER_PERSON_YEAR) * opening["working_share"]
        return opening
    real_opening_values = economy_port_year.opening_values
    with mock.patch.object(economy_port_year, "opening_values", with_ceiling):
        yield
