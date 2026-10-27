"""One-line forwarders from the old `Sim` names of finance to the finance module, for callers not yet in a module.

The screens, the project phases, the agent economy's port and the tests still say `sim.credit_limit()` or `sim.insolvent_years`;
each line goes when its last caller reads the view or sends the command itself."""
from sim.finance.api import FoundBank, NoteLenderPosting, constants
from . import money_units


class ForwardFinanceMixin:

	# the numbers other topics' code, the screens and the tests still read off the game (sim/finance/constants.py declares them)
	vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
	CREDIT_LINE_PER_REPUTATION_POINT = money_units.PricedInLabourHours("CREDIT_LINE_LABOUR_HOURS_PER_REPUTATION_POINT")
	CREDIT_LINE_PER_FOREST_HA = money_units.PricedInLabourHours("CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA")
	INSOLVENCY_FLOOR_MIN = money_units.PricedInLabourHours("INSOLVENCY_FLOOR_MIN_LABOUR_HOURS")

	# ---- the acting seat's debt ----

	def _debt_figure(self, name):
		return self.view("debt_status")()[name]

	@property
	def insolvent_years(self):
		return self._debt_figure("insolvent_years")

	@property
	def credit_frozen_until(self):
		return self._debt_figure("credit_frozen_until")

	@property
	def bondage_debt(self):
		return self._debt_figure("bondage_debt")

	@property
	def bondage_years_left(self):
		return self._debt_figure("bondage_years_left")

	@property
	def interest_paid(self):
		"""Everything the household has paid in interest; an attribute error before it first pays any."""
		paid = self._debt_figure("interest_paid")
		if paid is None:
			raise AttributeError("interest_paid")
		return paid

	# ---- the credit line and what can be spent ----

	def credit_limit(self, _rev=None, _upkeep=None, _capital=None):
		return self.view("credit_limit")(_rev, _upkeep, _capital)

	def credit_line_sought(self, _rev=None, _upkeep=None, _capital=None):
		return self.view("credit_line_sought")(_rev, _upkeep, _capital)

	def living_cost(self, _rev=None, _upkeep=None, _capital=None):
		return self.view("living_cost")(_rev, _upkeep, _capital)

	def bearable_part_of(self, amount):
		return self.view("bearable_part_of")(amount)

	def spending_power(self, kind="buy"):
		return self.view("spending_power")(kind)

	def funding_capacity(self):
		return self.view("funding_capacity")()

	def funding_breakdown(self):
		return self.view("funding_breakdown")()

	def committed_spend(self):
		return self.view("committed_cost")()

	# ---- the rate and what debt the income carries ----

	def debt_interest_rate(self):
		return self.view("debt_interest_rate")()

	def market_rate(self):
		return self.view("market_rate")()

	def market_credit_room(self, actor_id):
		return self.view("credit_room")(actor_id)

	def capital_market_report(self):
		return self.view("capital_market_report")()

	def dependants_beyond_means(self, living, revenue, upkeep, mine_cost=0.0):
		return self.view("dependants_beyond_means")(living, revenue, upkeep, mine_cost)

	def recurring_living_cost(self, revenue, upkeep):
		return self.view("recurring_living_cost")(revenue, upkeep)

	def recurring_net(self):
		return self.view("recurring_net")()

	def interest_on_arrears(self):
		return self.view("interest_on_arrears")()

	def sustainable_debt(self):
		return self.view("sustainable_debt")()

	def debt_service_forecast(self, draw):
		return self.view("debt_service_forecast")(draw)

	def stall_diagnosis(self):
		return self.view("stall_diagnosis")()

	def debt_bondage_term_years(self):
		return self.view("debt_bondage_term_years")()

	# ---- the lenders' books and a seat's bank ----

	def note_lender_posting(self, account, signed, label):
		self.send(NoteLenderPosting(account, signed, label))

	def seat_found_bank(self, capital):
		return self.send(FoundBank(capital))
