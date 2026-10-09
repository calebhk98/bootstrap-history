"""Households within a stratum, each with its own wealth: who in a body of people can put up a firm's stake.

A stratum is a headcount with a purse. Its savings are spread over its households as a Pareto distribution
(few hold much), so the richest household of a stratum, not its average member, funds a founding. What a
household has put into firms stays committed to it: `plan["committed"]` maps a household's rank (richest
first, as a string so a saved game keeps the key) to the money it has tied up. A household's free wealth is
its share of the stratum's gross savings (purse plus what is committed) less what it has committed."""
from typing import Any, Dict, Tuple

from .tuning import WEALTH_TAIL_INDEX


def committed_of(stratum: Any) -> Dict[str, float]:
	return stratum.record.plan.setdefault("committed", {})  # type: ignore[no-any-return]


def wealth_of_rank(stratum: Any, rank: int) -> float:
	"""The gross savings of the household that is `rank`th richest of the stratum (1 is the richest). The
	count of households holding at least a wealth falls as a power of it, and the average is the gross
	savings per member."""
	members = max(1.0, stratum.record.members)
	gross = max(0.0, stratum.money) + sum(committed_of(stratum).values())
	smallest = gross / members * (WEALTH_TAIL_INDEX - 1.0) / WEALTH_TAIL_INDEX
	return smallest * (members / rank) ** (1.0 / WEALTH_TAIL_INDEX)


def richest_free(stratum: Any) -> Tuple[int, float]:
	"""(rank, free wealth) of the household with most unspent wealth; rank 0 when no household is left."""
	committed = committed_of(stratum)
	members = int(max(1.0, stratum.record.members))
	unused = 1
	while str(unused) in committed:
		unused += 1
	ranks = [int(key) for key in committed] + ([unused] if unused <= members else [])
	best = (0, 0.0)
	for rank in sorted(ranks):
		free = max(0.0, wealth_of_rank(stratum, rank) - committed.get(str(rank), 0.0))
		if free > best[1]:
			best = (rank, free)
	return best


def personal_capital(stratum: Any) -> float:
	"""What the stratum's best-placed household can put up, never more than the stratum's purse."""
	return min(max(0.0, stratum.money), richest_free(stratum)[1])


def commit(stratum: Any, amount: float) -> int:
	"""The best-placed household puts `amount` into a firm; returns its rank."""
	rank = richest_free(stratum)[0]
	committed = committed_of(stratum)
	committed[str(rank)] = committed.get(str(rank), 0.0) + amount
	return rank


def release(stratum: Any, rank: int, amount: float) -> None:
	"""A firm closes and the household that put up `amount` has it free again."""
	committed = committed_of(stratum)
	left = committed.get(str(rank), 0.0) - amount
	if left > 1e-9:
		committed[str(rank)] = left
	else:
		committed.pop(str(rank), None)
