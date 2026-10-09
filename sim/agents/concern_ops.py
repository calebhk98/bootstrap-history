"""Running a concern: one rule for any actor that operates one (a firm, a player).

Plain functions over an actor and a world view. The actor needs `workforce`, `record`, `credit`,
`debit`, `capacity_of` and `opened_year_of`.
"""
from typing import Any

from . import firm_entry, ledger
from .edges import EDGE_CUSTOMERS, EDGE_LANDOWNERS, EDGE_SUPPLIERS, EDGE_WORKERS


def staff_concern(actor: Any, node_id: str, world: Any) -> float:
	"""Take on the people a concern needs from the shared pool; the share of them found, which is
	the share of its output that gets made."""
	found = 1.0
	capacity = actor.capacity_of(node_id)
	for trade, wanted in sorted(world.concern_staff(node_id).items()):
		wanted *= capacity
		free = world.free_fte(trade, actor.actor_id)
		if free is None:
			continue
		free -= actor.workforce.get(trade, 0.0)
		taken = min(wanted, max(0.0, free))
		actor.workforce[trade] = actor.workforce.get(trade, 0.0) + taken
		found = min(found, taken / wanted)
	return found


def operate_concern(actor: Any, node_id: str, world: Any, rivals: float) -> float:
	"""One year of a concern: staff it, take its takings, pay upkeep, wages, levy and royalty.
	Returns the year's margin."""
	capacity = actor.capacity_of(node_id)
	found = staff_concern(actor, node_id, world)
	actor.record.staffing[node_id] = found
	takings = found * world.concern_takings(node_id, actor.opened_year_of(node_id, world.year), rivals, capacity)
	upkeep = world.upkeep(node_id, capacity)
	wages = found * world.concern_wage_bill(node_id, capacity)
	ledger.transfer(world.edge(EDGE_CUSTOMERS), actor, takings, "takings")
	ledger.transfer(actor, world.edge(EDGE_SUPPLIERS), upkeep, "upkeep")
	if actor.record.country is None:
		world.pay_wages(actor, wages, "wages")
	else:
		ledger.transfer(actor, world.edge(EDGE_WORKERS), wages, "wages")
	levy = world.government().collect(actor, takings, world)
	royalty = world.collect_royalty(actor, node_id, takings)
	return takings - upkeep - wages - levy - royalty


def carry_concern(actor: Any, node_id: str, world: Any) -> float:
	"""Pay what running a concern costs whatever it sells: rent on the land it occupies and a manager's
	hours (the same costs an entrant weighs, firm_entry.carrying_cost). Returns the sum paid."""
	capacity = actor.capacity_of(node_id)
	rent = world.site_rent(node_id, capacity, actor.location())
	management = firm_entry.management_cost(world, node_id, capacity)
	ledger.transfer(actor, world.edge(EDGE_LANDOWNERS), rent, "site rent")
	if actor.record.country is None:
		world.pay_wages(actor, management, "management")
	else:
		ledger.transfer(actor, world.edge(EDGE_WORKERS), management, "management")
	return rent + management


def open_concern(actor: Any, node_id: str, world: Any) -> None:
	"""The actor begins running a concern it can make."""
	actor.concerns.add(node_id)
	actor.record.opened_year[node_id] = world.year


def close_concern(actor: Any, node_id: str) -> None:
	"""The actor stops running a concern and forgets its size and staffing."""
	actor.concerns.discard(node_id)
	actor.record.opened_year.pop(node_id, None)
	actor.record.capacity.pop(node_id, None)
	actor.record.staffing.pop(node_id, None)
	actor.record.margins.pop(node_id, None)
