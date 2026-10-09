"""Spin-offs: staff of a business who know a concern leave and found a rival that runs a copy of it.

How many consider leaving grows with the staff the concern keeps and the years it has run; each who does founds
a rival only where an entrant would earn (the same test as any entrant), so the market, not a count, stops them. The new firm learns what
the concern needs (the parent keeps all it knew), is funded as any entrant is (a stratum's founder, else the pooled capital). A patent on the concern is a risk the rival weighs (the state's reach times its margin), not a block.
"""
from typing import Any, List, Optional

from . import concern_ops, enforcement, firm_entry, ledger
from .edges import EDGE_POOLED_CAPITAL
from .records import ActorRecord
from .registry import register_spawner
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE, ENTRY_STAKE_BUFFER, VALUE_HORIZON_YEARS
from .tuning_spinoff import SPINOFF_CHANCE_PER_STAFF_YEAR, SPINOFF_MIN_YEARS


def know_how(node_id: str, world: Any, parent: Any) -> List[str]:
	"""The steps below `node_id` that the parent knows and the baseline does not, prerequisites first."""
	baseline = world.baseline_knowledge()
	chain: List[str] = []
	seen = set()

	def visit(current: str) -> None:
		if current in seen or current in baseline:
			return
		seen.add(current)
		for prerequisite in world.nodes[current].get("pre") or ():
			visit(prerequisite)
		chain.append(current)

	visit(node_id)
	return chain


def leavers_expected(parent: Any, node_id: str, world: Any) -> float:
	"""How many of the parent's staff in a year consider leaving to found a rival."""
	years = world.year - parent.opened_year_of(node_id, world.year)
	if years < SPINOFF_MIN_YEARS:
		return 0.0
	staff = sum(parent.workforce.values())
	return SPINOFF_CHANCE_PER_STAFF_YEAR * staff * years


def consider_spinoffs(registry: Any, world: Any) -> List[str]:
	"""Each business that runs a concern may lose staff who found rivals running it, one after another
	while a rival would pass the test any entrant does: it earns after what a firm carries, and a founder
	(or, with no strata, the pooled capital) puts up the whole stake."""
	founded: List[str] = []
	pool = [world.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE]
	for parent_id in sorted(registry.actors):
		parent = registry.actors[parent_id]
		if parent.kind not in ("firm", "player") or parent.record.exited_year is not None:
			continue
		for node_id in sorted(parent.concerns):
			expected_leavers = leavers_expected(parent, node_id, world)
			if expected_leavers <= 0.0:
				continue
			draw = world.rng_for(world.year, "spinoff", parent_id, node_id).random()
			leavers = int(expected_leavers) + (1 if draw < expected_leavers - int(expected_leavers) else 0)
			for _ in range(leavers):
				firm_id = _found_rival(registry, world, parent, node_id, pool)
				if firm_id is None:
					break
				founded.append(firm_id)
	return founded


def _found_rival(registry: Any, world: Any, parent: Any, node_id: str, pool: List[float]) -> Optional[str]:
	"""A rival of the parent founded into its concern, or None when an entrant would not earn enough."""
	rivals = registry.rivals_of(node_id, "")
	tile = firm_entry.firm_tile(registry, parent)
	expected = (firm_entry.expected_entry_gross(registry, world, node_id, rivals, 1.0)
				- world.upkeep(node_id) - world.concern_wage_bill(node_id)
				- firm_entry.carrying_cost(world, node_id, tile=tile))
	expected -= enforcement.expected_damages(world, "", node_id, expected)
	if expected <= 0.0:
		return None
	stake = world.copy_cost(node_id) * ENTRY_STAKE_BUFFER
	strata_exist = bool(registry.of_kind("stratum"))
	founders = firm_entry.founder_candidates(registry) if strata_exist else []
	founder = founders[0] if founders else None
	own, borrowed = firm_entry.stake_split(stake, founder, strata_exist, pool[0])
	if borrowed > 0.0 or expected * VALUE_HORIZON_YEARS <= stake or expected <= stake * world.market_rate():
		return None
	serial = len(registry.state.records) + 1
	while "firm:%d" % serial in registry.state.records:
		serial += 1
	firm_id = "firm:%d" % serial
	firm = registry.add(firm_id, ActorRecord(
		kind="firm", name=firm_id, target=node_id, last_margin=expected, founded_year=world.year,
		location=tile, country=parent.record.country, spun_off_from=parent.actor_id))
	firm.learn(know_how(node_id, world, parent), world)
	if founder is not None:
		firm.record.plan["founder"] = founder.actor_id
		ledger.transfer(founder, firm, own, "founding stake")
	else:
		pool[0] -= own
		ledger.transfer(registry.state.edge(EDGE_POOLED_CAPITAL), firm, own, EDGE_POOLED_CAPITAL)
	concern_ops.open_concern(firm, node_id, world)
	return firm_id


register_spawner("spinoffs", consider_spinoffs)
