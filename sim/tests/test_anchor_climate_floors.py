"""anchor_climate_floors: regression checks, run individually with `--only anchor_climate_floors`."""
from .harness import *  # noqa: F401,F403
from sim.engine import joint_allocation, market_demand, need_data
from sim.world import demand, need_demand

# The price solver's demand anchors face the floors the climate of the civilisation's tiles sets, the same basket
# the households of the engine's market and the economy are built on, not the data's flat defaults.

_civ = S.load_civ("rome_100ad")
_game = unopened_sim(civ="rome_100ad")
_anchors = joint_allocation.build_demand_anchors(_civ["id"], civilization=_civ)
_households = market_demand.household_basket(_game.civ, _game.world_map)
_floors = {need.need_id: need.subsistence_per_person for need in _households.needs}

check("the anchors' floors are the households' climate floors, need for need",
      all(abs(_anchors.model.subsistence[need] - floor) <= 1e-9 * max(1.0, abs(floor)) for need, floor in _floors.items()),
      (_anchors.model.subsistence, _floors))
_flat = need_demand.NeedDemandModel(
    need_data.load_needs(joint_allocation._ROOT), demand.production_data(), []).subsistence
check("...which differ from the data's flat defaults for the needs the climate sets",
      any(abs(_anchors.model.subsistence[need] - _flat[need]) > 1e-9 for need in _flat), (_anchors.model.subsistence, _flat))
