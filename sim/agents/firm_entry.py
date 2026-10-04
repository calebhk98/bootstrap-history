"""What it takes to found a firm: who funds the stake, what crowding adds to its cost, how easily the founder copies."""
from typing import Any, List, Optional, Tuple

from .tuning import ENTRY_EQUITY_SHARE, ENTRY_PREMIUM_PER_OPERATOR, FOUNDER_WEALTH_MULTIPLE, TACIT_SHARE_OF_COPYING


def entry_premium(copy_cost: float, operators: float) -> float:
	"""The fixed cost of finding a place in a market that `operators` already serve."""
	return copy_cost * ENTRY_PREMIUM_PER_OPERATOR * max(0.0, operators)


def personal_capital(stratum: Any) -> float:
	"""What one founder of this stratum can put up: a well-off member's share of its savings."""
	members = stratum.record.members
	if members <= 0.0 or stratum.money <= 0.0:
		return 0.0
	return min(stratum.money, stratum.money / members * FOUNDER_WEALTH_MULTIPLE)


def founder_candidates(registry: Any) -> List[Any]:
	"""Strata of the home country that are free to found a firm and hold savings, richest founder first."""
	free = [stratum for stratum in registry.of_kind("stratum")
			if stratum.record.exited_year is None and stratum.record.country is None
			and not stratum.is_bonded() and personal_capital(stratum) > 0.0]  # type: ignore[attr-defined]
	return sorted(free, key=lambda stratum: (-personal_capital(stratum), stratum.actor_id))


def copy_ease(founder: Optional[Any]) -> float:
	"""Share of a copy's chance a founder keeps: reading and measuring what is seen helps. A founder
	who is not a stratum's member (the pooled-capital rule) keeps all of it."""
	if founder is None:
		return 1.0
	literacy = min(1.0, max(0.0, founder.record.literacy))
	return 1.0 - TACIT_SHARE_OF_COPYING * (1.0 - literacy)


def stake_split(stake: float, founder: Optional[Any], strata_exist: bool, pooled_limit: float) -> Tuple[float, float]:
	"""(put up from savings, to borrow) for a stake. With strata the stake comes from the founder's
	savings and lenders back only a founder who puts up their share of it, so none is founded where
	no stratum holds that much; without strata, from the pooled capital."""
	if not strata_exist:
		pooled = min(stake, pooled_limit)
		return pooled, stake - pooled
	available = personal_capital(founder) if founder is not None else 0.0
	pooled = min(stake, available)
	if pooled < stake * ENTRY_EQUITY_SHARE:
		return pooled, float("inf")
	return pooled, stake - pooled
