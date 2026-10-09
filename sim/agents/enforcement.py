"""Enforcing a patent: the state backs the holder only as far as its reach, so infringing is a risk, not a block.

An unlicensed operator of a patented concern is found out each year with the chance the state's capacity gives;
a holder who finds one is paid the margin the infringer made from it. An entrant weighs the same odds as an
expected cost before it goes ahead."""
from typing import Any

from . import ledger


def unlicensed(entry: Any, actor_id: str) -> bool:
	"""Whether `actor_id` practises a patented concern without the holder's leave."""
	return entry is not None and entry["holder"] != actor_id and actor_id not in entry["licensees"]


def expected_damages(world: Any, actor_id: str, node_id: str, margin: float) -> float:
	"""What an unlicensed `actor_id` (empty for an entrant yet to exist) expects to pay a year to the holder: the state's reach times the margin it makes."""
	lookup = getattr(world, "patent_entry", None)
	entry = lookup(node_id) if lookup is not None else None
	if not unlicensed(entry, actor_id):
		return 0.0
	return float(world.state_capacity()) * max(0.0, margin)


def holder_actor(registry: Any, world: Any, holder_id: str) -> Any:
	"""The actor holding a patent: one in the registry, else a seat."""
	return registry.get(holder_id) or getattr(world, "seat_parties", lambda: {})().get(holder_id)


def enforce_patents(registry: Any, world: Any) -> float:
	"""Each unlicensed operator of a patented concern is caught with the chance of the state's capacity and
	pays its margin on the concern to the holder, never more than its purse; the total paid."""
	paid = 0.0
	for node_id in sorted(registry.concern_nodes()):
		entry = world.patent_entry(node_id)
		if entry is None:
			continue
		holder = holder_actor(registry, world, entry["holder"])
		if holder is None:
			continue
		for operator in registry.operators_of(node_id):
			if not unlicensed(entry, operator.actor_id):
				continue
			draw = world.rng_for(world.year, "enforcement", operator.actor_id, node_id).random()
			if draw >= world.state_capacity():
				continue
			damages = min(max(0.0, operator.money), max(0.0, operator.record.last_margin) / max(1, len(operator.concerns)))
			ledger.transfer(operator, holder, damages, "damages")
			paid += damages
	return paid
