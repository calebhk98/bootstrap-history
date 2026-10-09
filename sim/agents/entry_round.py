"""One entrant into a niche: the test every new firm passes, whatever the niche or the year."""
from typing import Any, List, Optional

from . import enforcement, firm_entry, imitation, ledger
from .edges import EDGE_POOLED_CAPITAL
from .firm import Firm
from .records import ActorRecord
from .tuning import ENTRY_EQUITY_SHARE, ENTRY_STAKE_BUFFER, VALUE_HORIZON_YEARS


class NicheEntry:
	"""Founds firms into one proven concern, one at a time, for as long as an entrant would earn after
	what a firm carries more than the capital it ties up would earn at the market's rate. Nothing caps
	how many a year: the takings they share, the costs they carry and the capital left to found them
	decide where it stops. `pool` is the year's pooled savings still free to found firms, shared by niches."""

	def __init__(self, registry: Any, world: Any, node_id: str, pool: List[float], strata_exist: bool) -> None:
		self.registry, self.world, self.node_id = registry, world, node_id
		self.pool, self.strata_exist = pool, strata_exist
		self.tile = firm_entry.firm_tile(registry, None)
		self.carried = firm_entry.carrying_cost(world, node_id, tile=self.tile)
		self.costs = world.upkeep(node_id) + world.concern_wage_bill(node_id) + self.carried
		probe = Firm("probe", ActorRecord(kind="firm", founded_year=world.year))
		self.chain = imitation.missing_chain(node_id, world, probe)
		self.plan = imitation.copy_plan(probe, self.chain, world) if self.chain else None

	def found(self, rivals: float, waiting: int) -> Optional[str]:
		"""The id of a firm founded into the niche, or None when no entrant would earn enough."""
		registry, world, node_id = self.registry, self.world, self.node_id
		if self.plan is None:
			return None
		expected = firm_entry.expected_entry_gross(registry, world, node_id, rivals, waiting + 1) - self.costs
		expected -= enforcement.expected_damages(world, "", node_id, expected)
		if expected <= 0:
			return None
		probe = Firm("probe", ActorRecord(kind="firm", last_margin=expected, founded_year=world.year))
		founders = firm_entry.founder_candidates(registry) if self.strata_exist else []
		founder = founders[0] if founders else None
		chance = imitation.copy_chance(self.chain, world) * firm_entry.copy_ease(founder)
		stake = self.plan["total"] * ENTRY_STAKE_BUFFER
		pooled, borrowed = firm_entry.stake_split(stake, founder, self.strata_exist, self.pool[0])
		if founder is None and pooled < stake * ENTRY_EQUITY_SHARE:
			return None  # the pooled savings are spent: lenders back no entrant who puts up too little
		if borrowed > probe.spare_credit(world):
			return None
		capital_cost = pooled * world.market_rate() + (
			borrowed * probe.rate_on_loan(world, borrowed) if borrowed > 0.0 else 0.0)
		if expected * VALUE_HORIZON_YEARS * chance <= self.plan["total"] or expected * chance <= capital_cost:
			return None
		serial = len(registry.state.records) + 1
		while "firm:%d" % serial in registry.state.records:
			serial += 1
		firm_id = "firm:%d" % serial
		firm = registry.add(firm_id, ActorRecord(
			kind="firm", name=firm_id, target=node_id, last_margin=expected, founded_year=world.year,
			location=self.tile))
		if founder is not None:
			firm_entry.fund_from(founder, firm, pooled)
		else:
			self.pool[0] -= pooled
			ledger.transfer(registry.state.edge(EDGE_POOLED_CAPITAL), firm, pooled, EDGE_POOLED_CAPITAL)
		return firm_id
