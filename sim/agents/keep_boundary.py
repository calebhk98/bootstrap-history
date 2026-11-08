"""The boundary of the keep table (`keep_table.py`): the strata's keep read into rows, the kernel run once, and the payments posted.

Python reads the rows (the owner of each bonded stratum, its people, the year's food price in its country, its allowance and its
purse) and posts the money in row order (`ledger.transfer` per payment: each posting is booked by the book, noted on both parties and
seen by the transfer hook). The kernel decides which payments the owner's purse covers; the rest go to `ledger.pay_up_to`."""
from typing import Any, List, Tuple

from sim.book import InsufficientFunds

from . import ledger
from .edges import EDGE_ECONOMY
from .keep_table import KEEPS, OWNERS, KeepOwners, Keeps, plan_keeps

KEEP_PURPOSE = "keep of bonded"


def keeper_rows(registry: Any) -> List[Tuple[Any, Any]]:
	"""(bonded stratum, its keeper) in id order, for each bonded stratum whose plan names an owner other than itself that exists."""
	rows = []
	for actor in registry.of_kind("stratum"):
		if not actor.is_bonded():
			continue
		owner = registry.actors.get(actor.neighbour_id(str(actor.record.plan.get("owner") or "")))
		if owner is not None and owner is not actor:
			rows.append((actor, owner))
	return rows


def pay_keeps(registry: Any, world: Any, top_up: bool) -> None:
	"""Each keeper pays the food of the bonded it holds: the part of the year's cost beyond the allowance (`top_up`), or all of it, after
	the bonded's labour product has been handed to the keeper (a settlement; the product is booked and zeroed)."""
	rows = keeper_rows(registry)
	if not rows:
		return
	owner_actors: List[Any] = []
	owner_row = {}
	for _actor, owner in rows:
		if owner.actor_id not in owner_row:
			owner_row[owner.actor_id] = len(owner_actors)
			owner_actors.append(owner)
	paid_here = {actor.actor_id for actor, _owner in rows}
	keeps = KEEPS.new_table(Keeps, len(rows), len(rows))
	owners = OWNERS.new_table(KeepOwners, len(owner_actors), len(owner_actors))
	for number, owner in enumerate(owner_actors):
		purses = getattr(owner, "purses", None)
		owners.known[number] = 0 if purses is None or owner.actor_id in paid_here else 1
		owners.purse[number] = 0.0 if purses is None else purses.purse(owner.account_id)
	for number, (actor, owner) in enumerate(rows):
		record = actor.record
		keeps.owner[number] = owner_row[owner.actor_id]
		keeps.members[number] = record.members
		keeps.cost_per_person[number] = registry.countries.world_for(actor, world).people.subsistence_cost_per_person_year()
		keeps.allowance[number] = record.allowance
		keeps.labour_product[number] = 0.0 if top_up else record.labour_product
		keeps.top_up[number] = 1 if top_up else 0
	plan_keeps(keeps, owners)
	for number, (actor, owner) in enumerate(rows):
		record = actor.record
		if not top_up and record.labour_product > 0.0:
			ledger.transfer(registry.state.edge(EDGE_ECONOMY), owner, record.labour_product, EDGE_ECONOMY)
			record.labour_product = 0.0
		due = float(keeps.due[number])
		if due <= 0.0:
			continue
		if keeps.covered[number]:
			try:
				ledger.transfer(owner, actor, due, KEEP_PURPOSE)
				record.allowance += due
				continue
			except InsufficientFunds:   # the book refused after all: the rule that pays what it can
				pass
		record.allowance += ledger.pay_up_to(owner, actor, due, KEEP_PURPOSE)   # a keeper pays what it can
