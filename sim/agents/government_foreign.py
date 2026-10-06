"""`ForeignGovernment`: the state of a country other than the founder's, kept deliberately simple.

It is its own kind, not `Government` with a country set: the home `Government` levies the people the
founder's economy models and the founder, and every loop over governments in the engine means the
home one. This one never sees them. Each year it takes the revenue its country's taxpayers yield (people the
simulation does not model actor by actor, so the money enters at the edge "edge:foreign_taxpayers"), pays its
army and officials (leaving at "edge:foreign_payroll_*"), keeps what is left, and copies the founder's
inventions it values through its country's scoped world, so distance and its own techniques apply.
"""
from typing import Any, Dict

from . import budget, ledger
from .base import RecordedActor
from .registry import register_actor_kind
from .tuning import GOVERNMENT_WORTH_SHARE_PER_GAIN
from .tuning_country import EARNER_SHARE_OF_POPULATION, RESERVE_YEARS_OF_NEED
from .values import invention_gains, weighted_gain

REVENUE_EDGE = "edge:foreign_taxpayers"
ARMY_PAY_EDGE = "edge:foreign_payroll_army"
OFFICIALS_PAY_EDGE = "edge:foreign_payroll_officials"


class ForeignGovernment(RecordedActor):
	kind = "foreign_government"

	def revenue(self, world: Any) -> float:
		"""What its taxpayers yield: earners, at the going labourer's pay, times the share taken and the
		state's capacity to collect it. A world that is not its country's scope yields nothing."""
		tax_share = getattr(world, "tax_share", None)
		if tax_share is None:
			return 0.0
		earners = world.population_total() * EARNER_SHARE_OF_POPULATION
		return earners * world.pay_per_person_year("labourer") * tax_share() * world.state_capacity()

	def standing_need(self, world: Any) -> Dict[str, float]:
		"""Money the army and the officials cost this year at the country's own pay."""
		soldiers = self.record.army if self.record.army > 0.0 else world.army_wanted()
		return {"army": soldiers * world.pay_per_person_year(budget.SOLDIER_TRADE),
				"administration": sum(line.money for line in budget.administration_line(world))}

	def imitation_worth(self, node_id: str, world: Any) -> float:
		gain = weighted_gain(invention_gains(world.nodes[node_id]), world.state_weights())
		return max(0.0, gain) * sum(self.record.revenue_by_form.values()) * GOVERNMENT_WORTH_SHARE_PER_GAIN

	def copy_budget(self, world: Any) -> float:
		"""Money above the reserve it holds against its standing need."""
		reserve = RESERVE_YEARS_OF_NEED * sum(self.record.need.values())
		committed = sum((1.0 - work["progress"]) * (work["money"] + work["labour_cost"]) for work in self.works.values())
		return max(0.0, self.money - reserve - committed)

	def pay_standing_need(self, world: Any) -> None:
		need = self.standing_need(world)
		share = budget.funded_share(sum(need.values()), self.money)
		if share > 0.0:
			ledger.transfer(self, world.edge(ARMY_PAY_EDGE), need["army"] * share, ARMY_PAY_EDGE)
			ledger.transfer(self, world.edge(OFFICIALS_PAY_EDGE), need["administration"] * share, OFFICIALS_PAY_EDGE)
		wanted = world.army_wanted()
		soldiers = self.record.army if self.record.army > 0.0 else wanted
		self.record.army = budget.army_next_year(soldiers, wanted, share)
		self.record.need = need
		self.record.unfunded = {name: money * (1.0 - share) for name, money in need.items()}

	def collect(self, payer: Any, taxable: float, world: Any) -> float:
		"""Levy an actor of its own country (a firm, a player) at the share it takes of every taxpayer;
		the amount taken."""
		tax_share = getattr(world, "tax_share", None)
		if tax_share is None:
			return 0.0
		levy = max(0.0, taxable) * tax_share() * world.state_capacity()
		ledger.transfer(payer, self, levy, "levy")
		return levy

	def advance(self, world: Any) -> None:
		"""One year: take the revenue, pay the standing need, then copy what is worth copying. Its staff
		are not drawn from the founder's labour pool."""
		taken = self.revenue(world)
		if taken > 0.0:
			ledger.transfer(world.edge(REVENUE_EDGE), self, taken, REVENUE_EDGE)
		self.record.revenue_by_form = {"taxpayers": taken}
		self.pay_standing_need(world)
		self.act(world)
		self.workforce.clear()   # copying staff are the country's own people, not the founder's labour pool


register_actor_kind("foreign_government", ForeignGovernment)
