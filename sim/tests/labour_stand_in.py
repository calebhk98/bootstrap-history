"""A stand-in world for `Labour` (a real civilisation file and a real `Population`), so labour rules run with no game built."""
from types import SimpleNamespace

from sim.prices import solve_prices_core

from sim.engine import data
from sim.geography import api as geography
from sim.world import demography


def stand_in_world(civ_id="rome_100ad", total=None):
    civ = data.load_civ(civ_id)
    population = demography.Population.stationary(float(civ["population"]) / 50.0, seed=1)
    if total is not None:
        shrink(population, total)
    household = SimpleNamespace(base_tile=None, employees={}, trades_created=set(), trade_schools={})
    return SimpleNamespace(
        workforce=household, society=SimpleNamespace(society_labour_hours={}, wage_tightness_factors={}),
        civ=civ, urban_fraction=lambda: float(civ.get("urban_fraction", 0.0)), home_tiles_held=lambda: geography.tiles_held(civ), people_by_tile=lambda: None, pop_scale=1.0,
        provided_town_population=lambda labour, tile, nominal_people: None, has_town_premiums=lambda: False,
        population=population, state=SimpleNamespace(household=household,
                                                     projects=SimpleNamespace(done=set())),
        held_and_running=lambda: frozenset(civ.get("starting_techs", ())), built_ways=lambda: {}, trades_absent=set(), wages=data.WAGES, trade_family=data.trade_family,
        literacy=lambda field: 0.05, HOURS_PER_PERSON_YEAR=2000.0, actor_staff_fte=lambda trade: 0.0, economy=SimpleNamespace(agent_people_by_trade=lambda: None),
        techniques_available_to=solve_prices_core.techniques_available_to,
        trade_registry={trade_id: {"family": trade.family, "training_years": trade.training_years, **trade.extra}
                        for trade_id, trade in data.TRADE_REGISTRY.items()})


def shrink(population, total):
    """Scale every age cohort so the nation holds `total` people."""
    factor = total / population.total
    population.children *= factor
    population.working_age *= factor
    population.elderly *= factor
