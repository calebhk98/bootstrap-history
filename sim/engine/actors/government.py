"""`Government`: a country's state as an actor.

It keeps a budget. Revenue is what its economy yields; spending is the army
and officials it keeps (`budget.py`), paid from the purse. A deficit comes out
of the reserve and then every line is cut by the same share. What it could not
pay is what it seeks from the taxpayers it can see. What is left of the purse
funds copying know-how it values by the gains its civilisation's priorities
weight (military, infrastructure, prestige, ...), through its policy.
"""
from typing import Any, Dict, List, Tuple

from . import budget, ledger
from .base import Actor, RecordedActor
from .tuning import GOVERNMENT_WORTH_SHARE_PER_GAIN
from .values import invention_gains, weighted_gain


class Government(RecordedActor):
	kind = "government"

	def imitation_worth(self, node_id: str, world: Any) -> float:
		gains = invention_gains(world.nodes[node_id])
		gain = weighted_gain(gains, world.state_weights())
		return max(0.0, gain) * world.state_revenue() * GOVERNMENT_WORTH_SHARE_PER_GAIN

	# ---- what it takes -------------------------------------------------------
	def levy_rates(self) -> Tuple[float, float]:
		"""(requisition, office) share of income it takes at full notice, from last assessment."""
		return self.record.levy_requisition_rate, self.record.levy_office_rate

	def assess(self, payer: Actor, taxable: float, world: Any) -> Tuple[float, Dict[str, float]]:
		"""What the state levies on `payer` from `taxable` income this year, by purpose.

		One rule for every taxpayer: the state sees a visible scale (staff, wealth,
		prominence), and the shortfall it must raise sets the rate.
		"""
		requisition, office = world.levy_shares(world.visible_scale_of(payer), payer.standing())
		parts = {"requisition": requisition * max(0.0, taxable), "office": office * max(0.0, taxable)}
		return sum(parts.values()), parts

	def collect(self, payer: Actor, taxable: float, world: Any) -> float:
		"""Levy `payer` and receive it; the amount taken."""
		levy, parts = self.assess(payer, taxable, world)
		if levy > 0.0:
			ledger.transfer(payer, self, levy, parts)
		return levy

	def military_ask(self, taxable: float, scale: float, world: Any) -> float:
		"""What the state asks of a militarily useful taxpayer in arms: its unfunded army need,
		in proportion to the taxpayer's part of the visible income, never past the ceiling."""
		unfunded = self.record.unfunded.get("army", 0.0)
		if unfunded <= 0.0 or self.record.levy_base <= 0.0:
			return 0.0
		own = world.notice_over(scale) * max(0.0, taxable)
		return min(budget.LEVY_RATE_CEILING * max(0.0, taxable), unfunded * own / self.record.levy_base)

	# ---- what it keeps up ---------------------------------------------------
	def pay_standing_need(self, world: Any) -> Tuple[List[budget.Line], float]:
		"""Take the year's revenue, pay what the purse covers of the standing need, and book the rest
		as unfunded. The goods it bought are this year's demand on the market."""
		self.credit(world.state_revenue(), "taxation")
		wanted = world.army_wanted()
		soldiers = self.record.army if self.record.army > 0.0 else wanted
		lines = budget.standing_lines(world, soldiers) + budget.concession_lines(world.group_claims())
		share = budget.funded_share(sum(line.money for line in lines), self.money)
		self.record.army = budget.army_next_year(soldiers, wanted, share)
		self.record.need = {line.name: line.money for line in lines}
		self.record.unfunded = {line.name: line.money * (1.0 - share) for line in lines}
		self.record.demand = {}
		for line in lines:
			if share > 0.0:
				self.debit(line.money * share, line.name)
			for commodity, tonnes in line.materials.items():
				self.record.demand[commodity] = self.record.demand.get(commodity, 0.0) + tonnes * share
		return lines, share

	def employ_standing(self, lines: List[budget.Line], share: float, world: Any) -> None:
		"""Staff of the lines it paid for, as far as they reach into the founder's labour market."""
		for line in lines:
			for trade, people in line.labour.items():
				self.workforce[trade] = self.workforce.get(trade, 0.0) + world.local_staff(trade, people * share)

	def seek_shortfall(self, lines: List[budget.Line], world: Any) -> None:
		"""Set the rate it takes from the income it can see so that the unfunded need is raised."""
		payers = world.visible_taxpayers()
		self.record.levy_base = sum(world.notice_over(scale) * income for scale, income in payers)
		kinds = {line.name: line.kind for line in lines}
		self.record.levy_requisition_rate, self.record.levy_office_rate = budget.levy_rates(
			self.record.unfunded, kinds, self.record.levy_base)

	def advance(self, world: Any) -> None:
		held = dict(self.workforce)
		lines, share = self.pay_standing_need(world)
		self.act(world)
		self.employ_standing(lines, share, world)
		self.seek_shortfall(lines, world)
		self.press_new_staff(held, world)
