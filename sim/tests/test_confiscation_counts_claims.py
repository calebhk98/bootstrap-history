"""A confiscation counts what the household is owed by other actors and takes it once the purse is empty, when a
reader and seizer are registered (sim/polity/state_demand.py). The polity module on plain values, no whole game."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.polity import state_demand
from sim.tests import polity_host


class Treasury:
	def __init__(self):
		self.received = 0.0

	def credit(self, amount, purpose):
		self.received += amount


class Purse(SimpleNamespace):
	def debit(self, amount, purpose):
		self.capital -= amount


def fixture(capital, owed):
	household = Purse(capital=capital)
	treasury = Treasury()
	owed_box = [owed]

	def reader(sim):
		return owed_box[0]

	def seizer(sim, amount, taker):
		seized = min(amount, owed_box[0])
		owed_box[0] -= seized
		taker.received += seized
		return seized

	module = polity_host.build(acting_balance=lambda: household.capital, legacy_acting_household=household, state_treasury=treasury)
	module.state_reach = lambda: 0.5
	return module, household, treasury, owed_box, reader, seizer


before = list(state_demand.WEALTH_CLAIMS)
state_demand.WEALTH_CLAIMS.clear()
try:
	sim, household, treasury, owed, reader, seizer = fixture(100.0, 300.0)
	_answer, demanded, taken = sim.answer_confiscation(0.5, "confiscation")
	check("with no claims registered only the purse is counted", demanded == 50.0 and taken == 50.0, (demanded, taken))

	sim, household, treasury, owed, reader, seizer = fixture(100.0, 300.0)
	state_demand.register_wealth_claims(reader, seizer)
	_answer, demanded, taken = sim.answer_confiscation(0.5, "confiscation")
	check("a registered claim is counted in what the state demands", demanded == 200.0, demanded)
	check("the purse pays first, then the claim", household.capital == 0.0 and owed[0] == 200.0 and taken == 200.0,
		  (household.capital, owed[0], taken))
	check("everything taken reached the treasury", treasury.received == taken, (treasury.received, taken))

	sim, household, treasury, owed, reader, seizer = fixture(100.0, 300.0)
	state_demand.WEALTH_CLAIMS.clear()
	state_demand.register_wealth_claims(reader, seizer)
	_answer, demanded, taken = sim.answer_confiscation(0.1, "confiscation")
	check("a small demand is met from the purse and leaves the claim alone", owed[0] == 300.0 and household.capital == 60.0,
		  (owed[0], household.capital))
finally:
	state_demand.WEALTH_CLAIMS[:] = before
