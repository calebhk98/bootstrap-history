"""What it takes to found a firm: who funds the stake, what it must carry, how easily the founder copies."""
from typing import Any, List, Optional, Tuple

from . import household_wealth, ledger
from .tuning import ENTRY_EQUITY_SHARE, ENTRANT_EXPECTATION_ADJUSTMENT_SHARE, MANAGEMENT_SPAN_OF_CONTROL, TACIT_SHARE_OF_COPYING


def management_cost(world: Any, node_id: str, capacity: float = 1.0) -> float:
	"""Yearly pay for the manager hours a concern run at `capacity` times its founding size needs:
	the hours of its staff over the span of control, paid as the best paid trade among its staff."""
	staff = world.concern_staff(node_id)
	people = sum(staff.values()) * capacity
	if people <= 0.0:
		return 0.0
	manager_wage = max(world.labour_market.quote(trade, 0.0) for trade in staff)
	return people / MANAGEMENT_SPAN_OF_CONTROL * world.hours_per_person_year * manager_wage


def firm_tile(registry: Any, actor: Optional[Any]) -> Optional[str]:
	"""The tile a firm's concerns stand on: where the firm was placed, else the home country's tile."""
	if actor is not None and actor.record.location is not None:
		return actor.record.location  # type: ignore[no-any-return]
	home = registry.actors.get("government:" + (registry.state.home_country or ""))
	return None if home is None else home.record.location  # type: ignore[no-any-return]


def carrying_cost(world: Any, node_id: str, capacity: float = 1.0, tile: Optional[str] = None) -> float:
	"""What a firm running a concern at `capacity` carries beyond the concern's upkeep and wages: the
	rent of the site on its tile and a manager's hours. The cost of winning customers is the agents'
	hours the merchants' terms charge per tonne a carrier lifts (merchant_terms.agent_cost_per_tonne);
	a sale in the firm's own market needs no carrier, so a firm carries nothing more for it, and where
	goods cross places the traders who carry them bear it."""
	return world.site_rent(node_id, capacity, tile) + management_cost(world, node_id, capacity)


def expected_takings(registry: Any, world: Any, node_id: str) -> float:
	"""The takings of a lone operator an entrant expects: last year's expectation moved part of the way
	to this year's takings, so a one-year spike in price does not draw a crowd of entrants. Revised
	once a year."""
	state = registry.state
	spot = world.entry_gross(node_id, 0.0, 1.0)
	if node_id not in state.expected_takings:
		state.expected_takings[node_id] = spot
	elif state.expected_takings_year.get(node_id) != world.year:
		previous = state.expected_takings[node_id]
		state.expected_takings[node_id] = previous + ENTRANT_EXPECTATION_ADJUSTMENT_SHARE * (spot - previous)
	state.expected_takings_year[node_id] = world.year
	return state.expected_takings[node_id]


def expected_entry_gross(registry: Any, world: Any, node_id: str, rivals: float, entrants: float) -> float:
	"""Yearly takings one more operator expects once `entrants` (itself included) join the `rivals`: the
	market's sharing as it stands, at the takings level entrants expect."""
	spot = world.entry_gross(node_id, rivals, entrants)
	spot_alone = world.entry_gross(node_id, 0.0, 1.0)
	if spot_alone <= 0.0:
		return spot
	return spot * expected_takings(registry, world, node_id) / spot_alone


def personal_capital(stratum: Any) -> float:
	"""What one founder of this stratum can put up: its best-placed household's free wealth."""
	return household_wealth.personal_capital(stratum)


def fund_from(founder: Any, firm: Any, amount: float) -> None:
	"""A household of the founding stratum puts `amount` into the firm; the firm remembers which and how much."""
	rank = household_wealth.commit(founder, amount)
	ledger.transfer(founder, firm, amount, "founding stake")
	firm.record.plan["founder"] = founder.actor_id
	firm.record.plan["founder_household"] = rank
	firm.record.plan["stake"] = amount


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
