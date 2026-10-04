"""Spin-offs: staff of a business who know a concern leave and found a rival that runs a copy of it.

The chance grows with the staff the concern keeps and the years it has run. The new firm learns what
the concern needs (the parent keeps all it knew), is funded from the society's pooled capital as any
entrant is, and no rival is founded on a concern while anyone holds a patent on it.
"""
from typing import Any, List

from . import concern_ops
from .records import ActorRecord
from .registry import register_spawner
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE, ENTRY_STAKE_BUFFER
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
	parent a year, and only where an entrant would earn and the pooled capital covers the stake."""
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
			expected = (world.entry_gross(node_id, registry.rivals_of(node_id, ""), 1.0)
						- world.upkeep(node_id) - world.concern_wage_bill(node_id))
			stake = world.copy_cost(node_id) * ENTRY_STAKE_BUFFER
			if expected <= 0.0 or stake > capital_limit or getattr(world, "patent_entry", lambda _node: None)(node_id):
				continue
			serial = len(registry.state.records) + 1
			while "firm:%d" % serial in registry.state.records:
				serial += 1
			firm_id = "firm:%d" % serial
			firm = registry.add(firm_id, ActorRecord(
				kind="firm", name=firm_id, target=node_id, last_margin=expected, founded_year=world.year,
				location=parent.record.location, country=parent.record.country, spun_off_from=parent_id))
			firm.learn(know_how(node_id, world, parent), world)
			firm.credit(stake, "edge:pooled capital")
			concern_ops.open_concern(firm, node_id, world)
			founded.append(firm_id)
			break
	return founded


register_spawner("spinoffs", consider_spinoffs)
