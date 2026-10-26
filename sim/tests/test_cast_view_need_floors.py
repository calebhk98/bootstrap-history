"""CastView.need_floor_costs_per_person_year and subsistence_cost_per_person_year on a stand-in self: the floors are the
economy's own tile-priced floors when it has them; the food floor is the food entry of those."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.agents.api import FOOD_NEED
from sim.actors.world_cast import CastView

from .world_stand_in import fake_needs


def stand_in(floors):
    return SimpleNamespace(needs=fake_needs(agent_need_floor_costs=lambda: floors),
                           need_floor_costs_per_person_year=lambda: floors)


economy_floors = {FOOD_NEED: 120.0, "shelter": 30.0}
check("the world's floors are the economy's own, need for need",
      CastView.need_floor_costs_per_person_year(stand_in(economy_floors)) == economy_floors)
check("the food floor is the economy's food entry",
      CastView.subsistence_cost_per_person_year(stand_in(economy_floors)) == 120.0)
