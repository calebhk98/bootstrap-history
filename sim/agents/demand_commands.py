"""The command by which an actor answers the state's demands."""
from typing import Any, Dict

from . import demand_answer
from .player_commands import CommandRejected, register_command


def answer_demand(player: Any, order: Dict[str, Any], world: Any) -> str:
	"""Comply with or refuse the state's requisitions from now on; says what a refusal would risk."""
	try:
		stance = demand_answer.checked_stance(order.get("stance"))
	except ValueError as reason:
		raise CommandRejected(str(reason)) from reason
	player.set_demand_stance(stance)
	odds = demand_answer.refusal_odds(1.0, world.state_capacity(), player.standing())
	return ("answering the state's demands by: %s. Refusing, the state enforces with a chance of %.0f%% "
			"and then takes the demand and %.0f%% more; otherwise nothing is taken"
			% (stance, 100.0 * odds["chance_enforced"], 100.0 * (odds["pay_if_enforced"] - 1.0)))


register_command("answer_demand", answer_demand)
