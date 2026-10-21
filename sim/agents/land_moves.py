"""Which shares of a tile's land change hands under confiscation and land reform: the planning, as plain data.

A move is (giver, receiver, share of the tile). The economy applies moves with its title rule (`titles.pass_title`), so a
holder only gives what he holds and a tenant who receives his lessor's land holds it outright. The state's own holdings and
any holder it names exempt are never taken from.

    confiscation:  each private holder gives `share` of what he holds to the state
    reform:        a holder above `cap` gives the excess, as far as he lets land out on the tile, to his tenants there
                   in proportion to the share each works
"""
from typing import Any, Collection, Dict, List, Mapping, NamedTuple, Optional, Sequence

EPSILON = 1e-9


class Move(NamedTuple):
	giver: str
	receiver: str
	share: float


def confiscation_moves(held: Mapping[str, float], state: str, share: float, exempt: Collection[str] = ()) -> List[Move]:
	"""Each private holder's `share` of his holding, to the state."""
	if share <= 0.0:
		return []
	return [Move(holder, state, min(1.0, share) * amount) for holder, amount in sorted(held.items())
			if holder != state and holder not in exempt and amount > EPSILON]


def reform_moves(held: Mapping[str, float], tenancies: Sequence[Mapping[str, Any]], cap: float,
				 exempt: Collection[str] = ()) -> List[Move]:
	"""The excess over `cap` of each holder, to the tenants he lets land to on the tile, by the share each works. What he
	does not let out cannot be given to tenants and stays with him."""
	moves: List[Move] = []
	for holder, amount in sorted(held.items()):
		excess = amount - max(0.0, cap)
		if holder in exempt or excess <= EPSILON:
			continue
		rows = [row for row in tenancies if row["lessor"] == holder and row["share"] > EPSILON]
		let_out = sum(row["share"] for row in rows)
		if let_out <= EPSILON:
			continue
		given = min(excess, let_out)
		moves += [Move(holder, row["tenant"], given * row["share"] / let_out) for row in sorted(rows, key=lambda row: row["tenant"])]
	return moves


def taken_from_private(moves: Sequence[Move], state: str) -> float:
	"""The share of the tile's land the moves took off holders other than the state."""
	return sum(move.share for move in moves if move.giver != state)


def by_tile(plan: Mapping[str, Sequence[Move]]) -> Dict[str, float]:
	"""Share of each tile's land the plan moves, for the grievance that follows."""
	return {tile: sum(move.share for move in moves) for tile, moves in plan.items() if moves}


def planned(held_by_tile: Mapping[str, Mapping[str, float]], tenancies_by_tile: Mapping[str, Sequence[Mapping[str, Any]]],
			state: str, confiscate: float, cap: Optional[float], exempt: Collection[str] = ()) -> Dict[str, List[Move]]:
	"""The moves on every tile: confiscation first, then reform on what holders are left holding."""
	plan: Dict[str, List[Move]] = {}
	for tile in sorted(held_by_tile):
		held = dict(held_by_tile[tile])
		moves = confiscation_moves(held, state, confiscate, exempt)
		for move in moves:
			held[move.giver] -= move.share
			held[move.receiver] = held.get(move.receiver, 0.0) + move.share
		if cap is not None:
			moves += reform_moves(held, tenancies_by_tile.get(tile, ()), cap, tuple(exempt) + (state,))
		if moves:
			plan[tile] = moves
	return plan
