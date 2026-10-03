"""Licensing a know-how from one actor to another: the fee and the royalty go through the ledger."""
from typing import Any, Dict

from . import imitation, ledger


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
	moves, when there is nothing the licensee still lacks."""
	chain = imitation.missing_chain(node_id, world, licensee)
	if not chain:
		return False
	ledger.transfer(licensee, licensor, fee, "licence")
	licensee.accept_licence(node_id, chain, world)
	return True


def royalty_due(takings: float, record: Dict[str, Any]) -> float:
	return max(0.0, takings) * float(record.get("royalty", 0.0))
