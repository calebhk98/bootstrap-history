"""What a licensed firm's takings owe the seats that licensed it an invention."""
from typing import Any, Callable, List, Mapping, Tuple

from sim.agents.api import licence

from . import builds


def seat_royalties_due(techniques: Mapping[str, Any], node_id: str, licensee_id: str, takings: float,
                       disclosures_of: Callable[[str], Mapping[str, Any]]) -> List[Tuple[str, float]]:
	"""(seat id, amount) for each seat (of `techniques`, what each holds and was granted) that built `node_id` and licensed it to `licensee_id` with a royalty on its
	takings, in the order the seats joined; a seat whose licence carries no royalty, or takings that are not
	positive, owe nothing and are left out. `disclosures_of` gives a seat's disclosures by node id."""
	owed = []
	for seat_id in builds.licensors_of(techniques, node_id, licensee_id, disclosures_of):
		record = disclosures_of(seat_id)[node_id]["licensees"][licensee_id]
		due = licence.royalty_due(takings, record)
		if due > 0.0:
			owed.append((seat_id, due))
	return owed


def seat_royalties_paid(owed: List[Tuple[str, float]], purse: float) -> List[Tuple[str, float]]:
	"""(seat id, amount) the licensee pays of what each seat is owed, in the order given, from a purse of `purse`:
	never more than the purse holds, so a firm short of money pays the first seats and the rest go unpaid."""
	left = max(0.0, purse)
	paid = []
	for seat_id, due in owed:
		amount = min(due, left)
		if amount > 0.0:
			paid.append((seat_id, amount))
			left -= amount
	return paid
