"""`Government`: a country's state as an actor.

It keeps a budget. Revenue is what its declared forms yield on the bases the economy
models, in coin or in kind (`revenue.py`, `government_stores.py`); spending is what it
keeps up (`budget.py`: army, officials, roads, public buildings, court, dole, works, collection, campaign, donative,
navy), paid from the purse. A deficit comes out of the reserve, then is
borrowed up to its credit ceiling (only once it holds the technology of public
debt). What it still lacks it meets by a choice among borrowing, cutting lines, deferring
pay, debasing, levying and demanding in kind (`fiscal_response.py`), as its policy picks. What is left of the purse
funds copying know-how it values by the gains its civilisation's priorities
weight (military, infrastructure, prestige, ...), through its policy.
"""
from typing import Any, Dict, List, Tuple

from sim.book import InsufficientFunds

from . import arrears, budget, demand_answer, headcount, ledger, state_enterprises, state_works
from .base import Actor, RecordedActor
from .government_coinage import Coinage
from .government_corvee import Corvee
from .government_credit import CreditRecord
from .government_enterprises import Enterprises
from .government_fiscal import Fiscal
from .government_granary import Granary
from .government_markets import Markets
from .government_stores import Stores
from .government_surplus import Surplus
from .purses import DEBT_FLOOR, Purses
from .edges import EDGE_PATRONAGE, EDGE_STATE_SPENDING
from .no_country_economy import NoCountryEconomy
from . import ruler
from .tuning import GOVERNMENT_WORTH_SHARE_PER_GAIN
from .tuning_spending import PUBLIC_BUILDING_LIFE_YEARS
from .values import invention_gains, weighted_gain


def _spend_what_it_can(state: Any, edge: Any, amount: float, purpose: str) -> None:
	"""Pay `amount` to the edge. Credit the lenders refuse (its limit, or the funds they hold) cuts the spending to the purse; a
	state with nothing in it spends nothing on the line this year."""
	try:
		ledger.transfer(state, edge, amount, purpose)
	except InsufficientFunds:
		affordable = max(0.0, state.money)
		if affordable > DEBT_FLOOR:
			ledger.transfer(state, edge, min(amount, affordable), purpose)


class Government(RecordedActor):
	"""A country's state. Its concerns are parts, each addressed as `government.<part>.<method>`:

	    corvee         labour dues: conscripts, works staffed and raised by corvee        (government_corvee.py)
	    credit_record  named lenders, the default record and the bond terms               (government_credit.py)
	    fiscal         how a shortfall is met: debasement, taxes in kind, rates, levers    (government_fiscal.py)
	    coinage        the decision to strike lighter coin                                (government_coinage.py)
	    enterprises    its own plants                                                      (government_enterprises.py)
	    granary        the grain reserve                                                   (government_granary.py)
	    markets        what it sells abroad and the markets it has closed                  (government_markets.py)
	    stores         revenue taken and the goods it holds                                (government_stores.py)
	    surplus        relief and works raised from money beyond the need                  (government_surplus.py)

	The record and the purse are the government's; the parts read and change them through it and reach their siblings
	through it. The methods here are the ones an `Actor` base class or a policy calls by name (`attach`, `default`,
	`credit_ceiling`, `rate_on_loan`, `borrowing_rate`, `sell_output`) and the year's order."""

	kind = "government"

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.corvee = Corvee(self)
		self.credit_record = CreditRecord(self)
		self.fiscal = Fiscal(self)
		self.coinage = Coinage(self)
		self.enterprises = Enterprises(self)
		self.granary = Granary(self)
		self.markets = Markets(self)
		self.stores = Stores(self)
		self.surplus = Surplus(self)

	def attach(self, purses: Purses) -> None:
		super().attach(purses)
		purses.named_lenders.name(self.account_id)

	def sell_output(self, world: Any) -> None:
		"""The state sells its plants' goods (`Actor.sell_output`, which the registry calls for every actor)."""
		self.enterprises.sell_output(world)

	def default(self, world: Any) -> None:
		"""The lenders' claims are written down; the loss goes on the state's record and its next borrowing costs more."""
		owed = self.debt()
		super().default(world)
		self.record.remembered_default_loss += owed
		self.record.defaults += 1

	def rate_on_loan(self, world: Any, amount: float) -> float:
		return super().rate_on_loan(world, amount) + self.credit_record.default_premium(self.debt() + amount)

	def borrowing_rate(self, world: Any) -> float:
		return super().borrowing_rate(world) + self.credit_record.default_premium(self.debt())

	@property
	def researches(self) -> bool:  # type: ignore[override]
		"""Only the founder's country's state originates research: it spends the founder's research hands. A
		country's state copies what it sees; its research would be priced at the founder's figures (retire: Complaint 676)."""
		return self.record.country is None

	def imitation_worth(self, node_id: str, world: Any) -> float:
		gains = invention_gains(world.setting.nodes[node_id])
		gain = weighted_gain(gains, world.setting.state_weights())
		return max(0.0, gain) * world.revenue.state_revenue() * GOVERNMENT_WORTH_SHARE_PER_GAIN

	def research_worth(self, node_id: str, world: Any) -> float:
		"""A state researches what its priorities weight (military, administration, ...), as it values copying it."""
		return self.imitation_worth(node_id, world)

	# ---- what it borrows against -------------------------------------------
	def credit_earning(self, world: Any) -> float:
		return world.revenue.state_revenue() + max(0.0, self.record.enterprise_margin)

	def credit_ceiling(self, world: Any) -> float:
		"""A state borrows only once it holds a technology declaring the `state_credit` mechanic."""
		return super().credit_ceiling(world) if world.credit.state_may_borrow(self) else 0.0

	def credit_standing(self, world: Any) -> float:
		"""Lenders trust a state as far as it can assess and collect."""
		return world.taxpayers.state_reach()

	# ---- what it takes -------------------------------------------------------
	def levy_rates(self) -> Tuple[float, float]:
		"""(requisition, office) share of income it takes at full notice, from last assessment."""
		return self.record.levy_requisition_rate, self.record.levy_office_rate

	def assess(self, payer: Actor, taxable: float, world: Any) -> Tuple[float, Dict[str, float]]:
		"""What the state levies on `payer` from `taxable` income this year, by purpose.

		One rule for every taxpayer: the state sees a visible scale (staff, wealth,
		prominence), and the shortfall it must raise sets the rate.
		"""
		requisition, office = world.taxpayers.levy_shares(world.taxpayers.visible_scale_of(payer), payer.stance.standing())
		parts = {"requisition": requisition * max(0.0, taxable), "office": office * max(0.0, taxable)}
		return sum(parts.values()), parts

	def collect(self, payer: Actor, taxable: float, world: Any) -> float:
		"""Levy `payer` and receive it; the amount taken."""
		levy, parts = self.assess(payer, taxable, world)
		if parts["requisition"] > 0.0 and payer.stance.demand_stance() != demand_answer.COMPLY:
			# a refused requisition is paid, with a penalty, only if the state can enforce it; a negotiated
			# one is paid in part, and in service, if the state takes the offer
			draw = world.setting.rng_for("demand", payer.actor_id, world.setting.year).random()
			answer = demand_answer.settle_demand(payer.stance.demand_stance(), parts["requisition"], world.taxpayers.state_reach(),
												 payer.stance.standing(), draw, payer.stance.service_worth())
			parts["requisition"] = answer["paid"] - answer["penalty"]
			if answer["penalty"] > 0.0:
				parts["penalty"] = answer["penalty"]
			if answer["service"] > 0.0:
				ledger.transfer(payer, world.setting.edge(EDGE_STATE_SPENDING), answer["service"], "service to the state")
			if answer["refused"]:
				payer.stance.set_defiance(demand_answer.defiance_after_refusal(payer.stance.defiance()))
			levy = sum(parts.values())
		if levy > 0.0:
			ledger.transfer(payer, self, levy, parts)
		return levy

	def military_ask(self, taxable: float, scale: float, world: Any) -> float:
		"""What the state asks of a militarily useful taxpayer in arms: its unfunded army need,
		in proportion to the taxpayer's part of the visible income, never past the ceiling."""
		return budget.military_ask_of(self.record.unfunded.get("army", 0.0), self.record.levy_base, world.taxpayers.notice_over(scale), taxable)

	def arrears_owed(self) -> float:
		"""Pay the state owes its army and officials from earlier years."""
		return arrears.total(self.record)

	def cannot_meet_own_need(self) -> bool:
		"""Whether last year's standing need went partly unpaid or unsupplied, or pay is still owed: such a state lends nothing."""
		return (sum(self.record.unfunded.values()) > 1e-9 or sum(self.record.unmet_goods.values()) > 1e-9
				or arrears.total(self.record) > 1e-9)

	# ---- what it keeps up ---------------------------------------------------
	def pay_standing_need(self, world: Any) -> Tuple[List[budget.Line], float]:
		"""Take the year's revenue, pay the arrears it owes, then what the purse covers of the standing need, and book the rest
		as unfunded. The goods it bought are this year's demand on the market."""
		self.pay_interest(world)
		self.stores.receive_revenue(world)
		arrears.settle(self, world)
		conscripts = self.corvee.conscript_years(world)
		wanted = max(budget.army_wanted(world), conscripts)
		soldiers = self.record.army if self.record.army > 0.0 else wanted
		others = headcount.people_in(budget.standing_lines(world, 0.0))
		soldiers, wanted = headcount.checked_army(world, self.record, wanted, soldiers, others)
		conscripts = min(conscripts, soldiers)
		self.corvee.serve_conscripts(conscripts, world)
		standing = budget.standing_lines(world, soldiers, conscripts) + budget.concession_lines(world.groups.group_claims())
		standing = self.corvee.staff_works_by_corvee(standing, world)
		self.record.material_need = state_enterprises.needs_of(standing)
		lines = self.stores.draw_stores(standing, world)
		self.granary.keep_granary(world)
		share = self.fiscal.meet_shortfall(lines, world)
		army_supplied = min([share] + [budget.supplied_share(line) for line in lines if line.name == "army"])
		self.record.army = budget.army_next_year(soldiers, wanted, army_supplied)
		self.record.unmet_goods = budget.unmet_goods(lines)
		self.record.need = {line.name: line.money for line in lines}
		self.record.unfunded = budget.unfunded_by_line(lines, share)
		arrears.owe(self.record, lines, share, self.fiscal.deferred_fraction(lines, share))
		state_works.wear(state_works.held(world), share, PUBLIC_BUILDING_LIFE_YEARS)
		if any(line.name == "donative" for line in lines):
			self.record.accession_due = False
		self.spend_on_lines(lines, share, world)
		return lines, share

	def spend_on_lines(self, lines: List[budget.Line], share: float, world: Any) -> None:
		"""Pay the funded `share` of each line: wages stay in the purse for the labour market's bids, other money out to the spending edge, and its
		materials as bids in the agent economy's book."""
		for line in lines:
			bought = line.material_cost if line.materials else 0.0   # its materials are bought with bids in the agent economy's book
			if share > 0.0:
				if not line.labour:   # a labour line's pay is offered in the labour market (sim/markets/port_staff.py)
					_spend_what_it_can(self, world.setting.edge(EDGE_STATE_SPENDING), (line.money - bought) * share, line.name)
			weight = sum(line.materials.values())
			for commodity, tonnes in line.materials.items():
				world.market.market_purchase(self.actor_id, commodity, tonnes * share, bought * share * tonnes / weight)

	def pay_patron(self, share: float, world: Any) -> None:
		"""Fund the founder as patron from what is left of the purse after the standing need.
		A state that left any of its need unpaid funds nobody, and nor does one whose country the economy keeps no pay or output
		for (it cannot say what to give)."""
		try:
			ask = world.patronage.patron_ask() if share >= 1.0 else 0.0
		except NoCountryEconomy:
			ask = 0.0
		grant = min(ask, max(0.0, self.money))
		self.record.patron_grant = grant
		if grant > 0.0:
			ledger.transfer(self, world.setting.edge(EDGE_PATRONAGE), grant, "patronage")

	def employ_standing(self, lines: List[budget.Line], share: float, world: Any) -> None:
		"""Post the places of the lines it paid for; the labour core hires for them (soldiers among them) and pays them."""
		for line in lines:
			for trade, people in line.labour.items():
				self.staff_wanted[trade] = self.staff_wanted.get(trade, 0.0) + people * share

	def seek_shortfall(self, lines: List[budget.Line], world: Any) -> None:
		"""Set the rate it takes from the income it can see so that the unfunded need is raised."""
		payers = world.taxpayers.visible_taxpayers()
		self.record.levy_base = sum(world.taxpayers.notice_over(scale) * income for scale, income in payers)
		kinds = {line.name: line.kind for line in lines}
		self.record.levy_requisition_rate, self.record.levy_office_rate = budget.levy_rates(
			self.fiscal.levy_sought(), kinds, self.record.levy_base)

	def accede(self, world: Any) -> None:
		"""The ruler ages a year and may die at his age band's mortality; his heir accedes, backed by the strongest faction
		and owing the army a donative until it is paid. Where the two strongest factions are evenly matched the runner-up
		may dispute the accession by arms (settled at the seat in the revolt phase)."""
		record = self.record
		record.ruler_age = ruler.opening_age() if record.ruler_age is None else record.ruler_age + 1.0
		rng = world.setting.rng_for("accession", self.actor_id, world.setting.year)
		if not ruler.dies(record.ruler_age, 1.0, rng.random()):
			return
		backing = world.groups.faction_backing()
		leader, challenger = ruler.contenders(backing)
		record.ruler_age = ruler.heir_age(record.ruler_age)
		record.ruler_backer = leader or ""
		record.accession_due = True
		disputed = challenger is not None and rng.random() < ruler.dispute_probability(backing)
		record.succession_challenger = challenger if disputed and challenger else ""

	def advance(self, world: Any) -> None:
		self.staff_wanted.clear()
		self.credit_record.fade_default_record()
		self.credit_record.set_bond_terms(world)
		self.purses.redeem_bonds(self.account_id)
		self.accede(world)
		lines, share = self.pay_standing_need(world)
		self.pay_patron(share, world)
		self.act(world)
		self.enterprises.run_enterprises(world)
		self.corvee.build_works_by_corvee(world)
		self.surplus.build_works(lines, world)
		self.employ_standing(lines, share, world)
		self.seek_shortfall(lines, world)
