"""Complaint 492 in a built game: Han's state holds the iron monopoly as a blast furnace it owns, staffed from the
labour pool, and its takings are the state's monopoly revenue."""

from .harness import *  # noqa: F401,F403

from sim.agents import state_enterprises
from sim.engine.agents_port import SimWorld

from .test_state_budget import unopened_sim

game = unopened_sim(civ="han_china_100ad")
state = game.state_treasury()
for _year in range(3):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)
plant = state.business.plant_of("blast_furnace")
check("Han's state runs a plant of the entry that makes cast iron", plant is not None and plant.state == "operating")
check("...which found its crew in the labour pool", plant.crew_found > 0.0 and state.workforce.get("furnaceman", 0.0) > 0.0, state.workforce)
check("...and whose takings are the state's monopoly revenue", plant.takings > 0.0
	  and state_enterprises.monopoly_revenue(state.record) >= plant.takings, (plant.takings, state.record.enterprise_takings))
check("an entry with no takings model (salt) is not opened", state.business.plant_of("mat_salt") is None)
