"""One-line forwarders from the old `Sim` names of finance to the finance module, for callers not yet in a module.

The screens, the project phases, the agent economy's port and the tests still say `sim.credit_limit()` or `sim.insolvent_years`;
each line goes when its last caller reads the view or sends the command itself."""
from sim.finance.api import NoteLenderPosting, constants
from . import money_units


class ForwardFinanceMixin:

	# the numbers other topics' code, the screens and the tests still read off the game (sim/finance/constants.py declares them)
	vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
	CREDIT_LINE_PER_FOREST_HA = money_units.PricedInLabourHours("CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA")
	INSOLVENCY_FLOOR_MIN = money_units.PricedInLabourHours("INSOLVENCY_FLOOR_MIN_LABOUR_HOURS")

	# ---- the acting seat's debt ----

	# ---- the credit line and what can be spent ----

	# ---- the rate and what debt the income carries ----

	# ---- the lenders' books and a seat's bank ----

	def note_lender_posting(self, account, signed, label):
		self.send(NoteLenderPosting(account, signed, label))
