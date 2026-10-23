"""Complaints 286 and 287: the map gives a state its frontier, its coast and its roads; the territory is called on tiles of named
regions. The army wanted is test_budget_view_army, the lines are test_state_budget_lines, patron funding is test_country_patronage."""

QUICK_TOPIC = True
from .harness import check

from sim.geography import api as geography_api, territory


# ---- the map gives a state its frontier, its coast and its roads ---------------------------------
held = territory.holdings(geography_api.tiles_of_regions(["italia", "gaul_germania"]))
check("a territory has a frontier, a coast and an internal road network, all in km",
      held.frontier_km > 0.0 and held.coast_km > 0.0 and held.road_km > 0.0, held)
bigger = territory.holdings(geography_api.tiles_of_regions(["italia", "gaul_germania", "britannia", "hispania"]))
check("holding more tiles means more road to keep up",
      bigger.road_km > held.road_km, (bigger.road_km, held.road_km))
alone = territory.holdings(geography_api.tiles_of_regions(["italia"]))
check("a state's road is the links between its own tiles, so an empty territory has none",
      territory.holdings([]).road_km == 0.0 and territory.holdings([]).frontier_km == 0.0
      and alone.road_km < held.road_km, alone)

