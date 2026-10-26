"""What the state's demands on a household are answered with: the claims a confiscation can count and take, and the player's
words for each way of answering. The rule is the one every actor is levied by (`sim/agents/demand_answer.py`)."""
from typing import Any, Callable, List, Tuple

from sim.agents.api import demand_answer

# stances that pay the demand in full and so draw no random number
PAYS_IN_FULL = (demand_answer.COMPLY, demand_answer.CONCEAL)

# Claims the acting household holds on other actors, which the state can count and seize: (reader, seizer) pairs.
# reader(game) -> money the household is owed; seizer(game, amount, taker) -> money actually handed to `taker`.
WEALTH_CLAIMS: List[Tuple[Callable[[Any], float], Callable[[Any, float, Any], float]]] = []


def register_wealth_claims(reader: Callable[[Any], float], seizer: Callable[[Any, float, Any], float]) -> None:
	"""Let a confiscation count (and, once the purse is empty, take) what the household is owed by other actors."""
	if (reader, seizer) not in WEALTH_CLAIMS:
		WEALTH_CLAIMS.append((reader, seizer))


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
