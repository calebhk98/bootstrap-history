"""`DeclaredKind`: a kind of actor whose behaviour is data, so a mod can bring a species without code.

A declaration is a body of people (or creatures) with a headcount, a purse, needs and a growth rule, run through the
same rules as any actor: it earns the pay of its trade from the labour market, buys the floor of each need it
declares at the going prices (so it competes with everyone for the same goods), and grows or shrinks by its declared
birth and death rates, deaths rising with the share of its vital needs left unmet. All money moves through
`ledger.transfer`. Declaration fields (all numbers are the mod author's own):
  needs        {need id: multiple of one person's floor cost of that need a year}
  vital_needs  the needs whose shortfall kills (default: every declared need)
  trade        the trade whose pay the members earn (optional), work_share their working share (default one)
  birth_rate, death_rate, famine_death_rate   yearly rates
The cast starts it with `params: {"members": N}` on a `cast.actors` entry naming the kind.
"""
from typing import Any, Dict, List

from . import ledger
from .base import RecordedActor
from .edges import EDGE_ECONOMY
from .registry import register_actor_kind
from .stratum_year import pay_tier, unmet

DECLARATIONS: Dict[str, Dict[str, Any]] = {}


class DeclaredKind(RecordedActor):
	kind = "declared"
	declaration: Dict[str, Any] = {}

	def imitation_candidates(self, world: Any) -> List[str]:
		return []

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	def learn(self, chain: List[str], world: Any) -> None:
		"""A declared kind holds no research tree."""

	def advance(self, world: Any) -> None:
		record, declaration = self.record, self.declaration
		members = record.members
		trade = declaration.get("trade")
		if trade and members > 0.0:
			wages = members * float(declaration.get("work_share", 1.0)) * world.pay_per_person_year(trade)
			if wages > 0.0:
				ledger.transfer(world.edge(EDGE_ECONOMY), self, wages, EDGE_ECONOMY)
		floor_costs = world.need_floor_costs_per_person_year()
		record.shortfall = {}
		for need_id in sorted(declaration["needs"]):
			need = members * float(declaration["needs"][need_id]) * floor_costs.get(need_id, 0.0)
			record.shortfall[need_id] = unmet(need, pay_tier(self, need, self.money, world))
		vital = declaration.get("vital_needs") or list(declaration["needs"])
		starved = sum(record.shortfall.get(need_id, 0.0) for need_id in vital) / max(1, len(vital))
		births = float(declaration["birth_rate"]) * (1.0 - starved)
		deaths = float(declaration["death_rate"]) + float(declaration["famine_death_rate"]) * starved
		record.last_growth = births - deaths
		record.members = max(0.0, members * (1.0 + record.last_growth))


def register_declared_kinds(declarations: Dict[str, Dict[str, Any]]) -> None:
	"""Make each declared kind id build a `DeclaredKind` with its declaration; safe to call again."""
	for kind, declaration in declarations.items():
		DECLARATIONS[kind] = declaration
		register_actor_kind(kind, type("DeclaredKind", (DeclaredKind,), {"kind": kind, "declaration": declaration}))
