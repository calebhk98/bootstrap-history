"""Complaint 314: people under arms leave the society's labour allocation, so the hours it can put into
farm work and trades fall by their hours and the unskilled wage moves by tightness."""
import pathlib

from .harness import *  # noqa: F401,F403

from sim.labour import labour_allocation, trade_data


def run_years(game, years):
    start = game.state.scenario.year
    for offset in range(1, years + 1):
        game.state.scenario.year = start + offset
        game.advance_actors(game.state.scenario.year)
        game._demographic_recovery(start + offset)


def with_army(share_of_working_age):
    """A game whose actors hold this share of the working age under arms (the state's own hiring
    raises only a few hundred in a year, so the staff is stated outright)."""
    game = sim()
    drawn = sorted(trade for trade in game.labour._world.wages if trade_data.drawn_from_unskilled_pool(trade))[0]
    held = share_of_working_age * game.population.working_age
    game.actor_staff_fte = lambda trade: held if trade == drawn else 0.0
    return game


def total_hours(game):
    return sum(game.state.economy.society_labour_hours.values())


unarmed, armed = with_army(0.0), with_army(0.2)
run_years(unarmed, 1)
run_years(armed, 1)
soldiers = armed.labour._people_under_arms()
check("a standing army holds people of an unskilled-pool trade", soldiers > 0.0, soldiers)
check("nobody is under arms without one", unarmed.labour._people_under_arms() == 0.0)
gap = total_hours(unarmed) - total_hours(armed)
expected = (unarmed.population.working_age - armed.population.working_age + soldiers) \
    * labour_allocation.HOURS_PER_FARM_WORKER_YEAR
check("the society's hours fall by the soldiers' hours", abs(gap - expected) < 1e-6 * total_hours(unarmed), (gap, expected))
check("hours stay positive under a large army", total_hours(armed) > 0.0)
farm = labour_allocation.FARM_TRADE
need = armed.state.economy.farm_hours_needed
have = armed.state.economy.society_labour_hours[farm]
check("farm hours still meet the farm need where the hours allow", have >= min(need, total_hours(armed)) * 0.99, (have, need))

run_years(unarmed, 3)
run_years(armed, 3)
fallback = trade_data.fallback_trade(armed.labour.wage_schedule().training_years, armed.labour._world.trade_family)
factor_armed = armed.labour.wage_schedule().tightness_factors.get(fallback, 1.0)
factor_unarmed = unarmed.labour.wage_schedule().tightness_factors.get(fallback, 1.0)
check("with the army out of production, the fallback trade's tightness factor ends higher",
      factor_armed > factor_unarmed, (factor_armed, factor_unarmed))

source = pathlib.Path(labour_allocation.__file__).read_text()
check("no content id literal in the allocation module",
      not any(literal in source for literal in ('"soldier"', "'soldier'", '"labourer"', "'labourer'")))
