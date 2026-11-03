"""A stand-in world for `Labour` (a real civilisation file and a real `Population`), so labour rules run with no game built."""
from types import SimpleNamespace

from sim.prices import solve_prices_core

from sim.engine import data
from sim.geography import api as geography
from sim.workforce.state import WorkforceSeat
from sim.world import demography


def stand_in_world(civ_id="rome_100ad", total=None):
    civ = data.load_civ(civ_id)
    population = demography.Population.stationary(float(civ["population"]) / 50.0, seed=1)
    if total is not None:
        shrink(population, total)
    household = WorkforceSeat(trade_schools={})      # the real seat: every field the labour code reads
    return SimpleNamespace(
        workforce=household, society=SimpleNamespace(society_labour_hours={}),
        scenario=SimpleNamespace(civ=civ, built_ways=lambda: {}),
        people=SimpleNamespace(urban_fraction=lambda: float(civ.get("urban_fraction", 0.0)), home_tiles_held=lambda: geography.tiles_held(civ),
                               people_by_tile=lambda: None, pop_scale=1.0, provided_town_population=lambda tile, nominal_people: None,
                               has_town_premiums=lambda: False, population=population),
        projects=SimpleNamespace(done=set(), done_year={}, granted=set(), operating=set(), active={}),
        finance=SimpleNamespace(balance=0.0, revenue=lambda: 0.0, upkeep=lambda: 0.0, living_cost=lambda: 0.0, rep_factor=lambda: 1.0, home_price_level=lambda: 1.0,
                              last_market_price_ratio=lambda material: 1.0, material_price_factor=lambda material: 1.0,   # prices at neutral
                              real_output_per_head=lambda: 1.0, price_index=1.0), standing=SimpleNamespace(founder_alive=True, bondage_years_left=0), set_farm_land=lambda hectares, quality: None,
        knowledge=SimpleNamespace(held_and_running=lambda: frozenset(civ.get("starting_techs", ())), literacy=lambda field: 0.05,
                                  STAFF_CAPACITY_SOURCES=[],      # no institution trains staff outright
                                  effect_sum=lambda channel, start=0.0: start, effect_terms=lambda channel: []),   # no technology effects
        trades=SimpleNamespace(trades_absent=set(), wages=data.WAGES, build_wage_schedule=data.schedule_of_civilisation, wage_index=1.0, trade_family=data.trade_family, HOURS_PER_PERSON_YEAR=2000.0,
                               techniques_available_to=solve_prices_core.techniques_available_to,
                               trade_registry={trade_id: {"family": trade.family, "training_years": trade.training_years, **trade.extra}
                                               for trade_id, trade in data.TRADE_REGISTRY.items()}),
        actors=SimpleNamespace(actor_staff_fte=lambda trade: 0.0), commands=SimpleNamespace(),
        economy=SimpleNamespace(unskilled_wage=lambda: None, agent_trades=lambda: None, agent_people_by_trade=lambda: None, agent_people_by_tile_and_trade=lambda: None, agent_hours_offered_at=lambda trade, tile: None, agent_working_hours=lambda: None, agent_wage_at=lambda trade, tile: None))


def shrink(population, total):
    """Scale every age cohort so the nation holds `total` people."""
    factor = total / population.total
    population.children *= factor
    population.working_age *= factor
    population.elderly *= factor
