"""People.need_floor_costs_per_person_year and subsistence_cost_per_person_year on a stand-in self: the floors are the
economy's own tile-priced floors when it has them; the food floor is the food entry of those."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.agents.api import FOOD_NEED
from sim.actors.world_people import People

from .world_stand_in import fake_needs


def stand_in(floors):
    return People(SimpleNamespace(needs=fake_needs(agent_need_floor_costs=lambda: floors)))


economy_floors = {FOOD_NEED: 120.0, "shelter": 30.0}
check("the world's floors are the economy's own, need for need",
      stand_in(economy_floors).need_floor_costs_per_person_year() == economy_floors)
check("the food floor is the economy's food entry",
      stand_in(economy_floors).subsistence_cost_per_person_year() == 120.0)
