"""Player commands for exchange, and the yearly answer of AI actors to the offers they hold."""
from typing import Any, Callable, Dict, List

from . import enforcement, exchange, joint_stock, patent, spinoff  # noqa: F401  (patent and spinoff register commands and spawners)
from .player_commands import CommandRejected, register_command
from .registry import register_spawner
from .tuning import VALUE_HORIZON_YEARS


def offer(player: Any, order: Dict[str, Any], world: Any) -> str:
	to = order.get("to")
	receiver = player.find_actor(to) if player.find_actor is not None and isinstance(to, str) else None
	made = exchange.make_offer(player, receiver, order.get("give") or {}, order.get("take") or {}, world)
	return "offered %s to %s" % (made["id"], made["to"])


def accept(player: Any, order: Dict[str, Any], world: Any) -> str:
	return exchange.accept(player, order.get("offer"), player.find_actor, world)


def decline(player: Any, order: Dict[str, Any], world: Any) -> str:
	return exchange.decline(player, order.get("offer"))


register_command("offer", offer)
register_command("accept", accept)
register_command("decline", decline)


# ---- the AI's answer ----------------------------------------------------------------------
def concern_worth(holder: Any, node_id: str) -> float:
	"""A concern's last margin over the valuation horizon; a share of the whole when not tracked singly."""
	record = holder.record
	margin = record.margins.get(node_id, record.last_margin / max(1, len(record.concerns)))
	return max(0.0, margin) * VALUE_HORIZON_YEARS


def side_worth(side: Dict[str, Any], taker: Any, holder: Any, world: Any, find_actor: Any = None) -> float:
	"""What `taker` counts the things in `side` (held by `holder`) as worth."""
	worth = side.get("money", 0.0)
	worth += sum(tonnes * world.material_price(material) for material, tonnes in side.get("stores", {}).items())
	valuer = getattr(taker, "imitation_worth", None)
	if valuer is not None:
		worth += sum(valuer(node_id, world) for node_id in side.get("knowledge", ()) if not taker.knows(node_id, world))
	if side.get("concern"):
		worth += concern_worth(holder, side["concern"])
	for node_id in set(side.get("patent", ())) | set(side.get("licence", ())):
		worth += max(valuer(node_id, world) if valuer is not None else 0.0, concern_worth(holder, node_id))
	if side.get("shares") and find_actor is not None:
		worth += joint_stock.shares_worth(side["shares"], find_actor)
	return worth


def answer_offers(actor: Any, find_actor: Callable[[str], Any], world: Any) -> List[str]:
	"""An AI actor accepts each offer that gives it more than it costs and declines the rest;
	returns the ids it answered."""
	if actor.record.controller != "ai":
		return []
	answered = []
	for offered in list(actor.record.offers):
		giver = find_actor(offered["from"])
		if giver is None:
			exchange.decline(actor, offered["id"])
			continue
		received = side_worth(offered["give"], actor, giver, world, find_actor)
		costs = {key: value for key, value in offered["take"].items() if key != "knowledge"}
		if received > side_worth(costs, giver, actor, world, find_actor):
			try:
				exchange.accept(actor, offered["id"], find_actor, world)
			except CommandRejected:
				continue
		else:
			exchange.decline(actor, offered["id"])
		answered.append(offered["id"])
	return answered


def exchange_answers(registry: Any, world: Any) -> List[str]:
	"""Yearly: lapse old offers, then let every AI actor answer what it holds. Founds no actors."""
	for actor_id in sorted(registry.actors):
		actor = registry.actors[actor_id]
		exchange.expire_offers(actor, world.year)
		answer_offers(actor, registry.get, registry.world_for(actor, world))
	return []


register_spawner("exchange_answers", exchange_answers)


def patent_enforcement(registry: Any, world: Any) -> List[str]:
	"""Yearly: holders pursue the operators of their patented concerns who have no licence. Founds no actors."""
	enforcement.enforce_patents(registry, world)
	return []


register_spawner("patent_enforcement", patent_enforcement)
