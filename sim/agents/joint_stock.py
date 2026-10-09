"""Joint-stock: an actor's equity is split into shares that others hold, trade, and draw dividends on.

Each holder's record keeps `holdings` (issuer id -> share of the issuer's equity); the issuer's record
keeps `issued`, the part held by others, and owns the rest. Shares move as the `shares` side of an
exchange offer, an issue being the issuer itself giving shares in itself. Each year a firm pays a part
of its last margin to its holders by share, through the ledger.
"""
import math
from typing import Any, Dict, Iterable, List

from . import ledger
from .registry import register_spawner
from .tuning import VALUE_HORIZON_YEARS
from .tuning_patent import DIVIDEND_PAYOUT_SHARE

EPSILON = 1e-9


def clean_shares(shares: Any) -> Dict[str, float]:
	"""`{issuer id: share}` checked and normalised; refuses (ValueError) what is malformed."""
	if not isinstance(shares, dict):
		raise ValueError("shares are {actor id: share of its equity}")
	kept = {str(issuer_id): float(share) for issuer_id, share in shares.items()}
	if any(not math.isfinite(share) or share < 0 or share > 1 for share in kept.values()):
		raise ValueError("a share is a part of an actor's equity, from 0 to 1")
	return {issuer_id: share for issuer_id, share in kept.items() if share > 0}


def held_in(actors: Iterable[Any], issuer_id: str) -> float:
	"""Share of `issuer_id`'s equity held by `actors`."""
	return sum(actor.record.holdings.get(issuer_id, 0.0) for actor in actors)


def holds_problem(holder: Any, shares: Dict[str, float]) -> str:
	"""Why `holder` cannot hand over these shares, or an empty string."""
	for issuer_id, share in sorted(shares.items()):
		if issuer_id == holder.actor_id:
			if share > 1.0 - holder.record.issued + EPSILON:
				return "has not that much equity left to issue"
		elif share > holder.record.holdings.get(issuer_id, 0.0) + EPSILON:
			return "holds too little of " + issuer_id
	return ""


def receives_problem(taker: Any, shares: Dict[str, float]) -> str:
	"""Why `taker` cannot take these shares, or an empty string."""
	for issuer_id, share in sorted(shares.items()):
		if issuer_id == taker.actor_id and share > taker.record.issued + EPSILON:
			return "cannot buy back more than it has issued"
	return ""


def hand_over(source: Any, target: Any, shares: Dict[str, float]) -> None:
	"""Move shares from `source` to `target`; an issuer giving its own raises what it has issued."""
	for issuer_id, share in sorted(shares.items()):
		if issuer_id == source.actor_id:
			source.record.issued += share
		else:
			left = source.record.holdings.get(issuer_id, 0.0) - share
			if left > EPSILON:
				source.record.holdings[issuer_id] = left
			else:
				source.record.holdings.pop(issuer_id, None)
		if issuer_id == target.actor_id:
			target.record.issued = max(0.0, target.record.issued - share)
		else:
			target.record.holdings[issuer_id] = target.record.holdings.get(issuer_id, 0.0) + share


def shares_worth(shares: Dict[str, float], find_actor: Any) -> float:
	"""What the shares are worth: the issuer's last margin over the valuation horizon, by share."""
	worth = 0.0
	for issuer_id, share in shares.items():
		issuer = find_actor(issuer_id)
		if issuer is not None:
			worth += share * max(0.0, issuer.record.last_margin) * VALUE_HORIZON_YEARS
	return worth


def issuers_among(registry: Any, world: Any) -> List[Any]:
	"""(issuer id, issuer, margin its dividends come from) for every actor in business that has outside
	shareholders: those in the registry, and the seats (a seat's margin is what its concerns earn over upkeep)."""
	found = []
	for issuer_id in sorted(registry.actors):
		issuer = registry.actors[issuer_id]
		if issuer.record.exited_year is None and issuer.record.issued > 0.0:
			found.append((issuer_id, issuer, issuer.record.last_margin))
	seat_margin = getattr(world, "seat_margin", None)
	for seat_id, party in sorted(getattr(world, "seat_parties", lambda: {})().items()):
		if seat_margin is not None and party.record.issued > 0.0:
			found.append((seat_id, party, seat_margin(seat_id)))
	return found


def issuers_among(registry: Any, world: Any) -> List[Any]:
	"""(issuer id, issuer, margin its dividends come from) for every actor in business that has outside
	shareholders: those in the registry, and the seats (a seat's margin is what its concerns earn over upkeep)."""
	found = []
	for issuer_id in sorted(registry.actors):
		issuer = registry.actors[issuer_id]
		if issuer.record.exited_year is None and issuer.record.issued > 0.0:
			found.append((issuer_id, issuer, issuer.record.last_margin))
	seat_margin = getattr(world, "seat_margin", None)
	for seat_id, party in sorted(getattr(world, "seat_parties", lambda: {})().items()):
		if seat_margin is not None and party.record.issued > 0.0:
			found.append((seat_id, party, seat_margin(seat_id)))
	return found


def pay_dividends(registry: Any, world: Any) -> float:
	"""Every actor with outside shareholders (in the registry, or a seat) pays them a part of its last margin
	by share, never more than its purse; returns the total paid."""
	paid = 0.0
	holders = dict(registry.actors)
	holders.update(getattr(world, "seat_parties", lambda: {})())
	for issuer_id, issuer, margin in issuers_among(registry, world):
		pool = min(DIVIDEND_PAYOUT_SHARE * max(0.0, margin), max(0.0, issuer.money))
		if pool <= 0.0:
			continue
		for holder_id in sorted(holders):
			share = holders[holder_id].record.holdings.get(issuer_id, 0.0)
			if share > 0.0 and holder_id != issuer_id:
				ledger.transfer(issuer, holders[holder_id], pool * share, "dividend")
				paid += pool * share
	return paid


def dividends(registry: Any, world: Any) -> List[str]:
	"""Yearly: pay dividends. Founds no actors."""
	pay_dividends(registry, world)
	return []


register_spawner("dividends", dividends)
