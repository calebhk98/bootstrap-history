"""A small economy built by hand, for scenario tests of `sim.economy` without the engine.

Three tiles in a row: a coastal town, a farm tile, and a tile where ore is worked. Goods: a grain
that feeds people, an ore dug by miners, and a metal smelted from it that is also the money's backing
and an ornament. `small_setup()` returns an `EconomySetup`; `run(setup, years)` opens an `Economy`
and steps it, returning the economy and each year's outcome. Nothing is read from data/, so a test
states every figure it depends on.
"""
import dataclasses

from sim.economy.economy import Economy
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY
from sim.economy.households_basket import Basket, NeedSpec
from sim.economy.protocols import YearInputs
from sim.economy.setup import EconomySetup, TradeSpec
from sim.economy.tile_costs import DRAUGHT_MODE, PACK_MODE, SEA_MODE, build_edges, handling_money_per_tonne_by_mode
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
        state_agent="state:fixture", tiles=the_tiles, edges=build_edges(the_tiles),
        carriage_rates={DRAUGHT_MODE: 0.002, PACK_MODE: 0.004, SEA_MODE: 0.0005},
        handling_rates=handling_money_per_tonne_by_mode(wages[LABOURER]),
        specs=specs(), recipes=recipes(), basket=basket(),
        trades={trade: TradeSpec(trade) for trade in wages},
        tax_forms=(), state_capacity=0.5, working_hours_per_year=2000.0, working_share=0.5,
        gini=0.4, opening_population_by_tile={TOWN: 4000.0, FARMS: 3000.0, HILLS: 1000.0},
        opening_prices=prices, opening_wages=wages, opening_rate=0.06,
        capital_tile=TOWN, port_tile=TOWN)
    return dataclasses.replace(setup, **changes) if changes else setup


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

