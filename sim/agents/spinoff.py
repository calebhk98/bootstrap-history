"""Spin-offs: staff of a business who know a concern leave and found a rival that runs a copy of it.

The chance grows with the staff the concern keeps and the years it has run. The new firm learns what
the concern needs (the parent keeps all it knew), is funded as any entrant is (a stratum's founder, else the pooled capital), and no rival is founded on a concern while anyone holds a patent on it.
"""
from typing import Any, List

from . import concern_ops, firm_entry, ledger
from .edges import EDGE_ENTRY_PREMIUM, EDGE_POOLED_CAPITAL
from .records import ActorRecord
from .registry import register_spawner
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE, ENTRY_STAKE_BUFFER, VALUE_HORIZON_YEARS
from .tuning_spinoff import SPINOFF_CHANCE_CAP, SPINOFF_CHANCE_PER_STAFF_YEAR, SPINOFF_MIN_YEARS


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


def spin_off_chance(parent: Any, node_id: str, world: Any) -> float:
	"""Yearly chance that staff of the parent's concern leave to found a rival."""
	years = world.year - parent.opened_year_of(node_id, world.year)
	if years < SPINOFF_MIN_YEARS:
		return 0.0
	staff = sum(parent.workforce.values())
	return min(SPINOFF_CHANCE_CAP, SPINOFF_CHANCE_PER_STAFF_YEAR * staff * years)


def consider_spinoffs(registry: Any, world: Any) -> List[str]:
	"""Each business that runs a concern may lose staff who found a rival running it; at most one a
	parent a year, and only where it passes the test any entrant does: it earns after the crowding
	premium, and a founder (or, with no strata, the pooled capital) puts up the whole stake."""
	founded: List[str] = []
	capital_limit = world.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE
	for parent_id in sorted(registry.actors):
		parent = registry.actors[parent_id]
		if parent.kind not in ("firm", "player") or parent.record.exited_year is not None:
			continue
		for node_id in sorted(parent.concerns):
			chance = spin_off_chance(parent, node_id, world)
			if chance <= 0.0 or world.rng_for(world.year, "spinoff", parent_id, node_id).random() >= chance:
				continue
			rivals = registry.rivals_of(node_id, "")
			expected = (world.entry_gross(node_id, rivals, 1.0)
						- world.upkeep(node_id) - world.concern_wage_bill(node_id))
			if expected <= 0.0 or getattr(world, "patent_entry", lambda _node: None)(node_id):
				continue
			# the same test as any entrant (registry.consider_entry): crowding premium, a founder's stake
			premium = firm_entry.entry_premium(world.copy_cost(node_id), rivals)
			stake = world.copy_cost(node_id) * ENTRY_STAKE_BUFFER + premium
			strata_exist = bool(registry.of_kind("stratum"))
			founders = firm_entry.founder_candidates(registry) if strata_exist else []
			founder = founders[0] if founders else None
			own, borrowed = firm_entry.stake_split(stake, founder, strata_exist, capital_limit)
			if borrowed > 0.0 or expected * VALUE_HORIZON_YEARS <= stake or expected <= stake * world.market_rate():
				continue
			serial = len(registry.state.records) + 1
			while "firm:%d" % serial in registry.state.records:
				serial += 1
			firm_id = "firm:%d" % serial
			firm = registry.add(firm_id, ActorRecord(
				kind="firm", name=firm_id, target=node_id, last_margin=expected, founded_year=world.year,
				location=parent.record.location, country=parent.record.country, spun_off_from=parent_id))
			firm.learn(know_how(node_id, world, parent), world)
			if founder is not None:
				firm.record.plan["founder"] = founder.actor_id
				ledger.transfer(founder, firm, own, "founding stake")
			else:
				ledger.transfer(registry.state.edge(EDGE_POOLED_CAPITAL), firm, own, EDGE_POOLED_CAPITAL)
			if premium > 0.0:
				ledger.transfer(firm, registry.state.edge(EDGE_ENTRY_PREMIUM), premium, EDGE_ENTRY_PREMIUM)
			concern_ops.open_concern(firm, node_id, world)
			founded.append(firm_id)
			break
	return founded


register_spawner("spinoffs", consider_spinoffs)
