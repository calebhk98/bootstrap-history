"""The founder's household answers the state's demands: the requisition and the supply levy it assesses.

The rule is the one every actor is levied by (`sim/agents/demand_answer.py`); this reads the household's
stance, the state's capacity and the household's protection off the game and rolls the enforcement.
"""
from typing import Any, Dict

from sim.agents.api import demand_answer


def answer_state_demand(sim: Any, amount: float) -> Dict[str, Any]:
	"""What the household pays on a demand of `amount` given how it has chosen to answer. A household
	that complies draws no random number, so complying leaves the game's stream as it was."""
	household = sim.state.household
	stance = household.demand_stance
	draw = sim.rng.random() if stance != demand_answer.COMPLY else 1.0
	return demand_answer.settle_demand(stance, amount, sim.state_capacity, household.protection, draw)


def set_household_stance(sim: Any, stance: str) -> str:
	"""Answer the state's demands by `stance` from now on; says what a refusal risks."""
	stance = demand_answer.checked_stance(stance)
	sim.state.household.demand_stance = stance
	odds = demand_answer.refusal_odds(1.0, sim.state_capacity, sim.state.household.protection)
	return ("you answer the state's demands by: %s. Refusing, the state enforces with a chance of %.0f%% and then "
			"takes the demand and %.0f%% more; otherwise nothing is taken"
			% (stance, 100.0 * odds["chance_enforced"], 100.0 * (odds["pay_if_enforced"] - 1.0)))
