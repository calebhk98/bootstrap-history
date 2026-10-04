"""Exchange: one actor offers another a bundle of things for a bundle of things.

An offer is plain data `{"id", "from", "to", "give", "take", "year", "expires"}` kept in the
receiver's record. Each side may hold `money`, `stores` ({material: tonnes}), `knowledge` ([node ids];
the receiver learns, the giver keeps) and `concern` (a node id; the concern, with its opened year and
size, moves), `patent` and `licence` ([node ids]; the right, or a licence to practise it, moves to the
receiver; see patent.py) and `shares` ({actor id: share of its equity}; see joint_stock.py). Acceptance checks both sides again and moves nothing unless everything still holds.
"""
import math
from typing import Any, Callable, Dict, List

from . import concern_ops, joint_stock, ledger, patent
from .player_commands import CommandRejected
from .tuning_exchange import OFFER_LIFETIME_YEARS

SIDE_KEYS = ("money", "stores", "knowledge", "concern", "patent", "licence", "shares")


def clean_side(side: Any) -> Dict[str, Any]:
	"""A side's contents checked and normalised; refuses what is malformed."""
	if not isinstance(side, dict):
		raise CommandRejected("each side of an offer is a mapping")
	unknown = sorted(set(side) - set(SIDE_KEYS))
	if unknown:
		raise CommandRejected("unknown things in an offer: " + ", ".join(map(str, unknown)))
	clean: Dict[str, Any] = {}
	amount = float(side.get("money") or 0.0)
	if not math.isfinite(amount) or amount < 0:
		raise CommandRejected("money must be a positive amount")
	if amount > 0:
		clean["money"] = amount
	stores = side.get("stores") or {}
	if not isinstance(stores, dict):
		raise CommandRejected("stores are {material: tonnes}")
	kept = {str(material): float(tonnes) for material, tonnes in stores.items()}
	if any(not math.isfinite(tonnes) or tonnes < 0 for tonnes in kept.values()):
		raise CommandRejected("tonnes must be positive")
	kept = {material: tonnes for material, tonnes in kept.items() if tonnes > 0}
	if kept:
		clean["stores"] = kept
	knowledge = side.get("knowledge") or []
	if not isinstance(knowledge, (list, tuple, set)) or not all(isinstance(node, str) for node in knowledge):
		raise CommandRejected("knowledge is a list of node ids")
	if knowledge:
		clean["knowledge"] = sorted(set(knowledge))
	if side.get("concern"):
		if not isinstance(side["concern"], str):
			raise CommandRejected("a concern is a node id")
		clean["concern"] = side["concern"]
	for key in ("patent", "licence"):
		nodes = side.get(key) or []
		if not isinstance(nodes, (list, tuple, set)) or not all(isinstance(node, str) for node in nodes):
			raise CommandRejected("%s is a list of node ids" % key)
		if nodes:
			clean[key] = sorted(set(nodes))
	if side.get("shares"):
		try:
			shares = joint_stock.clean_shares(side["shares"])
		except ValueError as reason:
			raise CommandRejected(str(reason))
		if shares:
			clean["shares"] = shares
	return clean


def holds_problem(holder: Any, side: Dict[str, Any], world: Any) -> str:
	"""Why `holder` cannot hand over `side` now, or an empty string."""
	if side.get("money", 0.0) > holder.money:
		return "has not enough money"
	for material, tonnes in sorted(side.get("stores", {}).items()):
		if tonnes > holder.record.stores.get(material, 0.0):
			return "has not enough " + material
	for node_id in side.get("knowledge", ()):
		if not holder.knows(node_id, world):
			return "does not know " + node_id
	if side.get("concern") and side["concern"] not in holder.concerns:
		return "does not run " + side["concern"]
	return patent.holds_problem(holder, side, world) or joint_stock.holds_problem(holder, side.get("shares", {}))


def receives_problem(taker: Any, incoming: Dict[str, Any], world: Any) -> str:
	"""Why `taker` cannot take `incoming`, or an empty string."""
	node_id = incoming.get("concern")
	if node_id:
		if node_id in taker.concerns:
			return "already runs " + node_id
		if not taker.knows(node_id, world) and node_id not in incoming.get("knowledge", ()):
			return "cannot make " + node_id
		if node_id not in incoming.get("patent", ()) and node_id not in incoming.get("licence", ()):
			reason = patent.blocked_reason(world, taker, node_id)
			if reason:
				return "needs a licence: " + reason
	return joint_stock.receives_problem(taker, incoming.get("shares", {}))


def problem(giver: Any, receiver: Any, give: Dict[str, Any], take: Dict[str, Any], world: Any) -> str:
	"""Why this deal cannot be done now, or an empty string."""
	for holder, side in ((giver, give), (receiver, take)):
		reason = holds_problem(holder, side, world)
		if reason:
			return "%s %s" % (holder.actor_id, reason)
	for taker, incoming in ((receiver, give), (giver, take)):
		reason = receives_problem(taker, incoming, world)
		if reason:
			return "%s %s" % (taker.actor_id, reason)
	return ""


def make_offer(giver: Any, receiver: Any, give: Dict[str, Any], take: Dict[str, Any], world: Any) -> Dict[str, Any]:
	"""Put an offer in the receiver's record, after checking the giver holds what it gives."""
	if receiver is None or receiver is giver:
		raise CommandRejected("no such counterparty")
	give, take = clean_side(give), clean_side(take)
	if not give and not take:
		raise CommandRejected("an offer needs something in it")
	reason = holds_problem(giver, give, world)
	if reason:
		raise CommandRejected(reason)
	giver.record.offer_serial += 1
	offer = {"id": "%s#%d" % (giver.actor_id, giver.record.offer_serial), "from": giver.actor_id,
			 "to": receiver.actor_id, "give": give, "take": take, "year": world.year,
			 "expires": world.year + int(OFFER_LIFETIME_YEARS)}
	receiver.record.offers.append(offer)
	return offer


def find_offer(receiver: Any, offer_id: Any) -> Dict[str, Any]:
	for offer in receiver.record.offers:
		if offer["id"] == offer_id:
			return offer
	raise CommandRejected("no such offer")


def move_concern(source: Any, target: Any, node_id: str, world: Any) -> None:
	opened = source.opened_year_of(node_id, world.year)
	capacity = source.record.capacity.get(node_id)
	concern_ops.close_concern(source, node_id)
	concern_ops.open_concern(target, node_id, world)
	target.record.opened_year[node_id] = opened
	if capacity is not None:
		target.record.capacity[node_id] = capacity


def hand_over(source: Any, target: Any, side: Dict[str, Any], world: Any) -> None:
	"""Move money, stores, a concern, patents and shares from `source` to `target`; knowledge is copied, not moved."""
	if side.get("money"):
		ledger.transfer(source, target, side["money"], "exchange")
	for material, tonnes in sorted(side.get("stores", {}).items()):
		source.record.stores[material] -= tonnes
		if source.record.stores[material] <= 0:
			del source.record.stores[material]
		target.record.stores[material] = target.record.stores.get(material, 0.0) + tonnes
	if side.get("concern"):
		move_concern(source, target, side["concern"], world)
	patent.hand_over(source, target, side)
	joint_stock.hand_over(source, target, side.get("shares", {}))


def accept(receiver: Any, offer_id: Any, find_actor: Callable[[str], Any], world: Any) -> str:
	"""Do the deal if both sides still hold everything; otherwise refuse and move nothing."""
	offer = find_offer(receiver, offer_id)
	giver = find_actor(offer["from"])
	if giver is None:
		raise CommandRejected("the offerer is gone")
	if world.year > offer["expires"]:
		raise CommandRejected("the offer has expired")
	reason = problem(giver, receiver, offer["give"], offer["take"], world)
	if reason:
		raise CommandRejected(reason)
	# knowledge first, so a concern can arrive with the know-how to run it
	for target, side in ((receiver, offer["give"]), (giver, offer["take"])):
		for node_id in side.get("knowledge", ()):
			target.learn([node_id], world)
	hand_over(giver, receiver, offer["give"], world)
	hand_over(receiver, giver, offer["take"], world)
	receiver.record.offers.remove(offer)
	return "accepted %s" % offer["id"]


def decline(receiver: Any, offer_id: Any) -> str:
	receiver.record.offers.remove(find_offer(receiver, offer_id))
	return "declined %s" % offer_id


def expire_offers(actor: Any, year: int) -> List[str]:
	"""Drop offers past their last year; returns their ids."""
	lapsed = [offer["id"] for offer in actor.record.offers if year > offer["expires"]]
	actor.record.offers[:] = [offer for offer in actor.record.offers if year <= offer["expires"]]
	return lapsed
