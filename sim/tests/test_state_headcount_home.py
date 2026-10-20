"""Complaint 602, home country: the founder's civilisation's state cannot keep an army larger than its people can spare."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


game = sim()
world = SimWorld(game)
hands = world.state_hands()
check("the home country's hands are its working age", hands.working_age == game.population.working_age, hands)

game.civ["standing_army"] = 10.0 * game.population.working_age
one_year(game)
record = game.state_treasury().record
booked = record.headcount["army"]
check("an army many times the working age is cut to the people free to serve, with the cause",
      record.army <= game.population.working_age and booked["shortfall"] > 0.0 and booked["cause"] == "working_age", (record.army, booked))

small = sim()
small.civ["standing_army"] = 0.001 * small.population.working_age
one_year(small)
check("a feasible home army is untouched", small.state_treasury().record.headcount["army"]["shortfall"] == 0.0,
      small.state_treasury().record.headcount)
