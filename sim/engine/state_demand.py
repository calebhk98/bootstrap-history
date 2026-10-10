"""The founder's household answers the state's demands: the requisition and the supply levy it assesses, and a confiscation.

The rule is the one every actor is levied by (`sim/agents/demand_answer.py`); this reads the household's
stance, the state's capacity and the household's protection off the game and rolls the enforcement.
"""
from typing import Any, Dict, Tuple

from sim.agents.api import demand_answer, edges, ledger

# stances that pay the demand in full and so draw no random number
_PAYS_IN_FULL = (demand_answer.COMPLY, demand_answer.CONCEAL)


def answer_state_demand(sim: Any, amount: float) -> Dict[str, Any]:
	"""What the household pays on a demand of `amount` given how it has chosen to answer. A household
	that complies draws no random number, so complying leaves the game's stream as it was. A refusal
	marks the household in the state's eyes and puts blame on it; a service offered in negotiation is paid
	to the people who render it."""
	household = sim.state.household
	stance = household.demand_stance
	draw = sim.rng.random() if stance not in _PAYS_IN_FULL else 1.0
	answer = demand_answer.settle_demand(stance, amount, sim.state_capacity, household.protection, draw,
										 household.service_offer)
	if answer["service"] > 0.0:
		sim.pay_edge(edges.EDGE_STATE_SPENDING, answer["service"], "service to the state")
	if answer["refused"]:
		household.defiance = demand_answer.defiance_after_refusal(household.defiance)
		household.scandal += demand_answer.blame_for_refusal(True)
	return answer


def answer_confiscation(sim: Any, fraction: float, cause: str) -> Tuple[Dict[str, Any], float, float]:
	"""The state demands `fraction` of the capital it can see (what the household has not hidden). The
	household answers like any demand; what is paid is taken to the treasury. Returns (the answer, what was
	demanded, what was taken)."""
	household = sim.state.household
	capital = household.capital
	demanded = demand_answer.visible_wealth(capital, household.concealed) * max(0.0, min(1.0, fraction))
	answer = answer_state_demand(sim, demanded)
	taken = 0.0
	if answer["paid"] > 0.0 and capital > 0.0:
		taken = sim.lose_capital(min(1.0, answer["paid"] / capital), cause, taker=sim.state_treasury())
	return answer, demanded, taken


def settle_household_year(sim: Any) -> Dict[str, float]:
	"""The household's yearly concealment and the state's forgetting of its refusals (as `demand_year` does for other actors)."""
	household = sim.state.household
	settled = {"concealed": 0.0, "cost": 0.0, "seized": 0.0, "found": 0.0}
	if household.demand_stance == demand_answer.CONCEAL or household.concealed > 0.0:
		draw = sim.rng.random()
		settled = demand_answer.settle_concealment(household.demand_stance, max(0.0, household.capital), sim.state_capacity,
												   household.protection, draw)
		if settled["cost"] > 0.0:
			sim.pay_edge(edges.EDGE_OFFICIALS, settled["cost"], "concealing wealth")
		if settled["seized"] > 0.0:
			ledger.transfer(household, sim.state_treasury(), settled["seized"], "wealth found hidden")
			household.log.append((sim.state.scenario.year, "The state found wealth you had hidden and took it with a penalty"))
		household.concealed = settled["concealed"]
	if household.defiance > 0.0:
		household.defiance = demand_answer.defiance_fading(household.defiance)
	return settled


def describe_stance(stance: str, capacity: float, standing: float, service: float = 0.0) -> str:
	"""What answering with `stance` risks, for the player: the odds of the answer, in words."""
	if stance == demand_answer.NEGOTIATE:
		odds = demand_answer.negotiation_odds(1.0, capacity, standing, service)
		return ("you negotiate: the state takes your offer with a chance of %.0f%%, and then you pay %.0f%% of the demand "
				"%s; otherwise it insists on the whole demand"
				% (100.0 * odds["chance_accepted"], 100.0 * odds["money_if_accepted"],
				   "and a service worth the rest" if odds["service_if_accepted"] > 0.0 else "(offer a service to improve the odds)"))
	if stance == demand_answer.CONCEAL:
		return ("you conceal: part of your wealth is held where the state cannot count it, so it assesses you "
				"as smaller; keeping it hidden costs a share a year, and if the state finds it, it takes the hoard "
				"and a penalty with a chance of %.0f%% a year"
				% (100.0 * demand_answer.CONCEALMENT_DETECTION_SHARE * demand_answer.enforcement_chance(capacity, standing)))
	odds = demand_answer.refusal_odds(1.0, capacity, standing)
	return ("you answer the state's demands by: %s. Refusing, the state enforces with a chance of %.0f%% and then "
			"takes the demand and %.0f%% more; otherwise nothing is taken, but the state marks you as defiant"
			% (stance, 100.0 * odds["chance_enforced"], 100.0 * (odds["pay_if_enforced"] - 1.0)))


def set_household_stance(sim: Any, stance: str, service: float = 0.0) -> str:
	"""Answer the state's demands by `stance` from now on, offering `service` (money's worth) when negotiating;
	says what the answer risks."""
	stance = demand_answer.checked_stance(stance)
	household = sim.state.household
	household.demand_stance = stance
	household.service_offer = max(0.0, float(service))
	return describe_stance(stance, sim.state_capacity, household.protection, household.service_offer)
