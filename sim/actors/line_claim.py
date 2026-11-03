"""A seat's own credit line among the lenders' capacities."""
from typing import List, Sequence, Tuple

Row = Tuple[str, float, float, float, float]   # (lender, offer, capacity, balance, ask), the economy's units


def with_own_claim(rows: Sequence[Row], claim: float) -> List[Row]:
	"""The lenders' rows with the borrower's own granted line given back: the clearing counted a line against its lenders' capacity
	(a room is claimed so no one else lends it), and the line's borrower draws on exactly that room. The claim comes back to the
	cheapest lenders first, each up to what it offered beyond its capacity now."""
	left = max(0.0, claim)
	given: List[Row] = []
	for lender, offer, capacity, balance, ask in rows:
		back = min(left, max(0.0, offer - capacity))
		left -= back
		given.append((lender, offer, capacity + back, balance, ask))
	return given
