"""A confiscation counts what the household is owed by other actors and takes it once the purse is empty, when a
reader and seizer are registered (sim/engine/state_demand.py). Small fixture, no whole game."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine import state_demand


class Treasury:
	def __init__(self):
		self.received = 0.0


def fixture(capital, owed):
	household = SimpleNamespace(capital=capital, concealed=0.0, demand_stance="comply", protection=0.0,
								service_offer=0.0, defiance=0.0, scandal=0.0)
	treasury = Treasury()
	owed_box = [owed]

	def lose_capital(fraction, cause, taker=None):
		lost = household.capital * fraction
		household.capital -= lost
		taker.received += lost
		return lost

	def reader(sim):
		return owed_box[0]

	def seizer(sim, amount, taker):
		seized = min(amount, owed_box[0])
		owed_box[0] -= seized
		taker.received += seized
		return seized

	sim = SimpleNamespace(state=SimpleNamespace(household=household), rng=SimpleNamespace(random=lambda: 0.5),
						  state_capacity=0.5, lose_capital=lose_capital, state_treasury=lambda: treasury,
						  pay_edge=lambda *args: None)
	return sim, household, treasury, owed_box, reader, seizer


before = list(state_demand.WEALTH_CLAIMS)
state_demand.WEALTH_CLAIMS.clear()
try:
	sim, household, treasury, owed, reader, seizer = fixture(100.0, 300.0)
	_answer, demanded, taken = state_demand.answer_confiscation(sim, 0.5, "confiscation")
	check("with no claims registered only the purse is counted", demanded == 50.0 and taken == 50.0, (demanded, taken))

	sim, household, treasury, owed, reader, seizer = fixture(100.0, 300.0)
	state_demand.register_wealth_claims(reader, seizer)
	_answer, demanded, taken = state_demand.answer_confiscation(sim, 0.5, "confiscation")
	check("a registered claim is counted in what the state demands", demanded == 200.0, demanded)
	check("the purse pays first, then the claim", household.capital == 0.0 and owed[0] == 200.0 and taken == 200.0,
		  (household.capital, owed[0], taken))
	check("everything taken reached the treasury", treasury.received == taken, (treasury.received, taken))

	sim, household, treasury, owed, reader, seizer = fixture(100.0, 300.0)
	state_demand.WEALTH_CLAIMS.clear()
	state_demand.register_wealth_claims(reader, seizer)
	_answer, demanded, taken = state_demand.answer_confiscation(sim, 0.1, "confiscation")
	check("a small demand is met from the purse and leaves the claim alone", owed[0] == 300.0 and household.capital == 60.0,
		  (owed[0], household.capital))
finally:
	state_demand.WEALTH_CLAIMS[:] = before
