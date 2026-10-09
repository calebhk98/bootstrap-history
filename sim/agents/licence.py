"""Licensing a know-how from one actor to another: the fee and the royalty go through the ledger."""
from typing import Any, Dict, Optional

from . import imitation, ledger, patent


def terms_problem(licensee: Any, fee: float, royalty: float) -> str:
	"""Why these terms cannot be offered to this licensee, or an empty string."""
	if fee < 0.0 or not 0.0 <= royalty < 1.0:
		return "a fee cannot be negative and a royalty is a share of takings, from 0 up to but not including 1"
	if royalty > 0.0 and licensee.kind != "firm":
		return "a royalty is a share of takings, and only a firm has takings; a state pays a fee"
	if licensee.money < fee:
		return "the licensee cannot pay the fee"
	return ""


def grant(licensor: Any, licensee: Any, node_id: str, fee: float, world: Any) -> bool:
	"""The licensee pays `fee` to the licensor and can make `node_id` at once. False, and nothing
	moves, when there is nothing the licensee still lacks or when someone else holds the patent."""
	entry = getattr(world, "patent_entry", lambda _node: None)(node_id)
	if entry is not None and entry["holder"] != getattr(licensor, "actor_id", None):
		return False
	chain = imitation.missing_chain(node_id, world, licensee)
	if not chain:
		return False
	ledger.transfer(licensee, licensor, fee, "licence")
	licensee.accept_licence(node_id, chain, world)
	patent.note_licence(licensor, licensee, node_id)
	return True


def live_patent(actors: Any, node_id: str, year: int) -> Optional[Dict[str, Any]]:
	"""The live patent on `node_id` held by one of `actors`, with its holder's id, or None."""
	return patent.entry_among(actors, node_id, year)


def royalty_due(takings: float, record: Dict[str, Any]) -> float:
	return max(0.0, takings) * float(record.get("royalty", 0.0))


def collect_patent_royalty(world: Any, find_holder: Any, firm: Any, node_id: str, takings: float) -> float:
	"""A firm licensed under a patent pays the holder the royalty agreed on its takings from the concern, never
	more than its purse, while the patent lives; the amount paid. `find_holder(id)` gives the holder actor."""
	owed = firm.record.royalty_owed.get(node_id)
	holder = find_holder(owed["holder"]) if owed else None
	entry = holder.record.patents.get(node_id) if holder is not None else None
	if entry is None or not patent.live(entry, world.year):
		return 0.0
	due = min(royalty_due(takings, {"royalty": owed["rate"]}), max(0.0, firm.money))
	ledger.transfer(firm, holder, due, "licence")
	return due
