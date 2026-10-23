"""Scenarios for Complaint 314 in a whole game: a standing army held by the actors leaves the society's labour allocation,
so a Rome game's farm still gets its hours. The rules (hours fall by the soldiers' hours, the fallback trade ends
tighter) are in test_soldiers_leave_production."""
from .harness import *  # noqa: F401,F403

from sim.labour import labour_allocation, trade_data


def run_years(game, years):
    start = game.state.scenario.year
    for offset in range(1, years + 1):
        game.state.scenario.year = start + offset
        game.advance_actors(game.state.scenario.year)
        game._demographic_recovery(start + offset)


def with_army(share_of_working_age):
    """A game whose actors hold this share of the working age under arms nationwide, as the
    nationwide staff count labour reads (Complaints/426)."""
    game = sim()
    drawn = sorted(trade for trade in game.labour._world.wages if trade_data.drawn_from_unskilled_pool(trade))[0]
    held = share_of_working_age * game.population.working_age
    game.actor_staff_nationwide = lambda trade: held if trade == drawn else 0.0
    game.army_held_nationwide = held
    return game


def total_hours(game):
    return sum(game.state.economy.society_labour_hours.values())


armed = with_army(0.2)
run_years(armed, 1)
# The engine's own count: the government's army, not the slice of it in the founder's pool.
real = unopened_sim()
treasury = real.state_treasury()
treasury.record.army = 0.1 * real.population.working_age
check("the engine's nationwide staff count carries the government's whole army",
      abs(real.labour._people_under_arms() - treasury.record.army) < 1e-6 * treasury.record.army,
      (real.labour._people_under_arms(), treasury.record.army))
farm = labour_allocation.FARM_TRADE
need = armed.state.holdings.farm_hours_needed
have = armed.state.economy.society_labour_hours[farm]
check("farm hours still meet the farm need where the hours allow", have >= min(need, total_hours(armed)) * 0.99, (have, need))
