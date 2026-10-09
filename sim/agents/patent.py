"""Patents: an exclusive right to an invention, held by an actor for a term, that it can sell or licence.

The right is plain data on the holder's record: `patents[node_id] = {"granted", "expires", "licensees"}`.
A state grants it only where it knows the institution (`world.state_grants_patents`), and anyone else who
would run the concern needs the holder's licence. `world.patent_entry(node_id)` is the live right as
`{"holder", "expires", "licensees"}`, or None.
"""
from typing import Any, Dict, Iterable, List, Optional

from .player_commands import CommandRejected, register_command
from .tuning_patent import PATENT_TERM_YEARS


def live(entry: Dict[str, Any], year: int) -> bool:
	return year <= entry["expires"]


def entry_among(actors: Iterable[Any], node_id: str, year: int) -> Optional[Dict[str, Any]]:
	"""The live patent on `node_id` held by one of `actors`, with its holder's id, or None."""
	for actor in sorted(actors, key=lambda each: each.actor_id):
		entry = actor.record.patents.get(node_id)
		if entry is not None and live(entry, year):
			return dict(entry, holder=str(actor.actor_id))
	return None


def holder_of(world: Any, node_id: str) -> Optional[str]:
	entry = world.patent_entry(node_id)
	return entry["holder"] if entry is not None else None


def blocked_reason(world: Any, actor: Any, node_id: str) -> str:
	"""Why `actor` may not practise `node_id` for want of a licence, or an empty string."""
	lookup = getattr(world, "patent_entry", None)
	entry = lookup(node_id) if lookup is not None else None
	if entry is None or entry["holder"] == actor.actor_id or actor.actor_id in entry["licensees"]:
		return ""
	return "%s holds the patent on %s and has not licensed it" % (entry["holder"], node_id)


def apply(actor: Any, node_id: str, world: Any) -> str:
	"""Ask the state for an exclusive right to an invention the actor holds; refuses with the reason."""
	if node_id not in world.nodes:
		raise CommandRejected("no such node")
	if not world.state_grants_patents(actor):
		raise CommandRejected("no state here knows how to grant a patent")
	if node_id in world.baseline_knowledge() or not actor.knows(node_id, world):
		raise CommandRejected("you can patent only an invention you hold")
	if getattr(world, "disclosure_mode", lambda _node: "")(node_id) == "publish":
		raise CommandRejected("it is already published")
	holder = holder_of(world, node_id)
	if holder is not None:
		raise CommandRejected("%s already holds the patent on %s" % (holder, node_id))
	entry = {"granted": world.year, "expires": world.year + int(PATENT_TERM_YEARS), "licensees": []}
	actor.record.patents[node_id] = entry
	return "patented %s until year %d" % (node_id, entry["expires"])


def holds_problem(holder: Any, side: Dict[str, Any], world: Any) -> str:
	"""Why `holder` cannot hand over the patents or licences in `side`, or an empty string."""
	for key in ("patent", "licence"):
		for node_id in side.get(key, ()):
			entry = holder.record.patents.get(node_id)
			if entry is None or not live(entry, world.year):
				return "does not hold a live patent on " + node_id
	return ""


def hand_over(source: Any, target: Any, side: Dict[str, Any]) -> None:
	"""Move each patent of `side` to `target` with its term; add `target` to the licensees of each licence."""
	for node_id in side.get("patent", ()):
		entry = source.record.patents.pop(node_id)
		entry["licensees"] = [each for each in entry["licensees"] if each != target.actor_id]
		target.record.patents[node_id] = entry
	for node_id in side.get("licence", ()):
		licensees = source.record.patents[node_id]["licensees"]
		if target.actor_id not in licensees:
			licensees.append(target.actor_id)


def note_licence(licensor: Any, licensee: Any, node_id: str) -> None:
	"""A licence from the holder lets the licensee practise the patented invention."""
	entry = getattr(getattr(licensor, "record", None), "patents", {}).get(node_id)
	if entry is not None and licensee.actor_id not in entry["licensees"]:
		entry["licensees"].append(licensee.actor_id)


def patent_command(player: Any, order: Dict[str, Any], world: Any) -> str:
	node_id = order.get("node")
	if not isinstance(node_id, str) or not node_id:
		raise CommandRejected("no node given")
	return apply(player, node_id, world)


register_command("patent", patent_command)
