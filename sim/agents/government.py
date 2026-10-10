"""`Government`: a country's state as an actor.

It keeps a budget. Revenue is what its declared forms yield on the bases the economy
models, in coin or in kind (`revenue.py`, `government_stores.py`); spending is what it
keeps up (`budget.py`: army, officials, roads, public buildings, court, dole, works, collection, campaign, donative,
navy), paid from the purse. A deficit comes out of the reserve, then is
borrowed up to its credit ceiling (only once it holds the technology of public
debt), and only then is every line cut by the same share. What it could not
pay is what it seeks from the taxpayers it can see. What is left of the purse
funds copying know-how it values by the gains its civilisation's priorities
weight (military, infrastructure, prestige, ...), through its policy.
"""
from typing import Any, Dict, List, Tuple

from . import budget, demand_answer, ledger, state_works
from .base import Actor, RecordedActor
from .government_coinage import CoinageMixin
from .government_granary import GranaryMixin
from .government_stores import StoresMixin
from .edges import EDGE_PATRONAGE, EDGE_STATE_SPENDING
from .government_surplus import SurplusMixin
from .tuning import GOVERNMENT_WORTH_SHARE_PER_GAIN
from .tuning_spending import ACCESSION_PROBABILITY_PER_YEAR, PUBLIC_BUILDING_LIFE_YEARS
from .values import invention_gains, weighted_gain


class Government(CoinageMixin, GranaryMixin, StoresMixin, SurplusMixin, RecordedActor):
	kind = "government"

	def imitation_worth(self, node_id: str, world: Any) -> float:
		gains = invention_gains(world.nodes[node_id])
		gain = weighted_gain(gains, world.state_weights())
		return max(0.0, gain) * world.state_revenue() * GOVERNMENT_WORTH_SHARE_PER_GAIN

	# ---- what it borrows against -------------------------------------------
	def credit_earning(self, world: Any) -> float:
		return world.state_revenue()

	def credit_ceiling(self, world: Any) -> float:
		"""A state borrows only once it holds a technology declaring the `state_credit` mechanic."""
		return super().credit_ceiling(world) if world.state_may_borrow(self) else 0.0

	def credit_standing(self, world: Any) -> float:
		"""Lenders trust a state as far as it can assess and collect."""
		return world.state_capacity()

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
		if parts["requisition"] > 0.0 and payer.demand_stance() != demand_answer.COMPLY:
			# a refused requisition is paid, with a penalty, only if the state can enforce it; a negotiated
			# one is paid in part, and in service, if the state takes the offer
			draw = world.rng_for("demand", getattr(payer, "actor_id", ""), world.year).random()
			answer = demand_answer.settle_demand(payer.demand_stance(), parts["requisition"], world.state_capacity(),
												 payer.standing(), draw, payer.service_worth())
			parts["requisition"] = answer["paid"] - answer["penalty"]
			if answer["penalty"] > 0.0:
				parts["penalty"] = answer["penalty"]
			if answer["service"] > 0.0:
				ledger.transfer(payer, world.edge(EDGE_STATE_SPENDING), answer["service"], "service to the state")
			if answer["refused"]:
				payer.set_defiance(demand_answer.defiance_after_refusal(payer.defiance()))
			levy = sum(parts.values())
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
		self.pay_interest(world)
		self.receive_revenue(world)
		wanted = world.army_wanted()
		soldiers = self.record.army if self.record.army > 0.0 else wanted
		standing = budget.standing_lines(world, soldiers) + budget.concession_lines(world.group_claims())
		lines = self.draw_stores(standing, world)
		self.keep_granary(world)
		share = budget.funded_share(sum(line.money for line in lines), self.money + self.credit_ceiling(world))
		self.record.army = budget.army_next_year(soldiers, wanted, share)
		self.record.need = {line.name: line.money for line in lines}
		self.record.unfunded = {line.name: line.money * (1.0 - share) for line in lines}
		state_works.wear(state_works.held(world), share, PUBLIC_BUILDING_LIFE_YEARS)
		if any(line.name == "donative" for line in lines):
			self.record.accession_due = False
		for line in lines:
			bought = line.material_cost if line.materials else 0.0   # its materials are bought with bids in the agent economy's book
			if share > 0.0:
				if line.labour:
					world.pay_wages(self, (line.money - bought) * share, line.name)   # the state's pay reaches its people
				else:
					ledger.transfer(self, world.edge(EDGE_STATE_SPENDING), (line.money - bought) * share, line.name)
			weight = sum(line.materials.values())
			for commodity, tonnes in line.materials.items():
				world.market_purchase(self.actor_id, commodity, tonnes * share, bought * share * tonnes / weight)
		return lines, share

	def pay_patron(self, share: float, world: Any) -> None:
		"""Fund the founder as patron from what is left of the purse after the standing need.
		A state that left any of its need unpaid funds nobody."""
		ask = world.patron_ask() if share >= 1.0 else 0.0
		grant = min(ask, max(0.0, self.money))
		self.record.patron_grant = grant
		if grant > 0.0:
			ledger.transfer(self, world.edge(EDGE_PATRONAGE), grant, "patronage")

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

	def accede(self, world: Any) -> None:
		"""A new ruler accedes with a yearly chance, and owes the army a donative until it is paid."""
		draw = world.rng_for("accession", self.actor_id, world.year).random()
		if draw < ACCESSION_PROBABILITY_PER_YEAR:
			self.record.accession_due = True

	def advance(self, world: Any) -> None:
		held = dict(self.workforce)
		self.accede(world)
		lines, share = self.pay_standing_need(world)
		self.decide_debasement(world)
		self.pay_patron(share, world)
		self.act(world)
		self.build_works(lines, world)
		self.employ_standing(lines, share, world)
		self.seek_shortfall(lines, world)
		self.press_new_staff(held, world)
