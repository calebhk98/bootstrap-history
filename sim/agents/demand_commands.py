"""The command by which an actor answers the state's demands."""
from typing import Any, Dict

from . import demand_answer
from .player_commands import CommandRejected, register_command


def answer_demand(player: Any, order: Dict[str, Any], world: Any) -> str:
	"""Answer the state's demands from now on by complying, refusing, negotiating (`service`, money's worth of
	work offered with the smaller sum) or concealing wealth; says what the answer would risk."""
	try:
		stance = demand_answer.checked_stance(order.get("stance"))
		service = max(0.0, float(order.get("service") or 0.0))
	except (TypeError, ValueError) as reason:
		raise CommandRejected(str(reason)) from reason
	player.set_demand_stance(stance)
	player.record.service_offer = service
	capacity, standing = world.state_capacity(), player.standing()
	if stance == demand_answer.NEGOTIATE:
		odds = demand_answer.negotiation_odds(1.0, capacity, standing, service)
		return ("answering the state's demands by: negotiating. The state takes your offer with a chance of %.0f%% and "
				"then you pay %.0f%% of the demand; otherwise it insists on the whole" % (
					100.0 * odds["chance_accepted"], 100.0 * odds["money_if_accepted"]))
	if stance == demand_answer.CONCEAL:
		return ("answering the state's demands by: concealing. Part of your wealth is held where the state cannot "
				"count it, so it assesses you as smaller; keeping it hidden costs a share a year, and a state that "
				"finds it takes the hoard and a penalty")
	odds = demand_answer.refusal_odds(1.0, capacity, standing)
	return ("answering the state's demands by: %s. Refusing, the state enforces with a chance of %.0f%% "
			"and then takes the demand and %.0f%% more; otherwise nothing is taken, but the state marks you as defiant"
			% (stance, 100.0 * odds["chance_enforced"], 100.0 * (odds["pay_if_enforced"] - 1.0)))


register_command("answer_demand", answer_demand)
