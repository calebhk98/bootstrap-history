"""home_floors_from_economy: regression checks, run individually with `--only home_floors_from_economy`."""
from .harness import *  # noqa: F401,F403
from sim.engine.agents_port import SimWorld

# What a person's floor of each need costs, as strata and the state read it, comes from the economy's own tile
# prices once it has opened (the engine's goods market answers only while it opens). Slow: it opens the economy.

_game = sim(civ="rome_100ad")
_game.economy.open_agent()
_world = SimWorld(_game)
_floors = _world.need_floor_costs_per_person_year()
_economy_floors = _game.economy.agent.need_floor_costs_per_person_year()

check("the economy prices a floor for at least the food need", bool(_economy_floors) and min(_economy_floors.values()) > 0.0,
      _economy_floors)
check("the world's floors are the economy's own, need for need", _floors == _economy_floors, (_floors, _economy_floors))
check("the food floor is the subsistence cost the strata read",
      _world.subsistence_cost_per_person_year() == _economy_floors.get("food", _world.subsistence_cost_per_person_year()),
      _world.subsistence_cost_per_person_year())
