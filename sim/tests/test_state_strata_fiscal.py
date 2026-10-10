"""Complaints 286 and 315: a state taxes what the bodies of people it governs earn, and a surplus beyond its
reserve goes to named people (relief of the hunger its strata report, then works), by `ledger.transfer`, so no
money appears or vanishes between actors."""
from .harness import *  # noqa: F401,F403

from sim.agents import revenue
from sim.agents.api import Government, Stratum, stratum_id
from sim.agents.records import ActorRecord
from sim.tests.agents_fake_world import FakeWorld

sim = unopened_sim   # legacy: pins the engine's budget by stratum; the agent-economy budget is test_economy_agent_state.py


class FiscalWorld(FakeWorld):
	"""A world with a country's strata and the questions a state asks about them."""

	def __init__(self):
		super().__init__()
		self.strata = []
		self.forms = []
		self.state = None
		self.food_cost, self.housing_cost = 100.0, 50.0

	def country_strata(self):
		return self.strata

	def revenue_forms(self):
		return self.forms

	def government(self):
		return self.state

	def subsistence_cost_per_person_year(self):
		return self.food_cost

	def need_floor_costs_per_person_year(self):
		return {"food": self.food_cost, "shelter": self.housing_cost}

	def pay_per_person_year(self, trade):
		return 1000.0

	def national_people(self, trade):
		return 1.0e6

	def local_staff(self, trade, people):
		return people

	def revenue_assessments(self):
		return revenue.assess(self)


def make_stratum(name, members, earned, money, hungry=0.0):
	body = Stratum(stratum_id("home", name), ActorRecord(kind="stratum", stratum=name, members=members, money=money))
	body.record.income["edge:economy"] = earned
	body.record.income["migration"] = 7.0e9   # a transfer between bodies is not earned
	body.record.shortfall = {"food": hungry, "shelter": hungry}
	return body


def make_world(money=0.0):
	world = FiscalWorld()
	world.state = Government("government:home", ActorRecord(kind="government", money=money))
	world.strata = [make_stratum("rich", 1.0e3, 1.0e6, 5.0e6), make_stratum("poor", 1.0e5, 2.0e6, 1.0e6, hungry=0.5)]
	return world


LEVY = {"form": "income_levy", "basis": "stratum_income", "rate": 0.1}

# ---- a form on the bodies' earned income is collected from them, once a year -----------------------
world = make_world()
world.forms = [LEVY]
assessed = revenue.assess(world)[0]
check("a levy on income is the rate times what the bodies earned, never what they were handed",
      abs(assessed.money - 0.1 * 3.0e6) < 1e-6, assessed.money)
check("each payer is named, so the money moves between actors", len(assessed.payers) == 2, assessed.payers)
state, rich, poor = world.state, world.strata[0], world.strata[1]
before = state.money + sum(body.money for body in world.strata)
state.receive_revenue(world)
check("the state received what its payers lost", abs(state.money - 0.1 * 3.0e6) < 1e-6, state.money)
check("no money appeared: the state's gain is the strata's loss",
      abs(state.money + sum(body.money for body in world.strata) - before) < 1e-6, state.money)
check("the tax is booked as taxation on the state and the payers", state.record.income.get("taxation", 0.0) > 0.0
      and rich.record.outlays.get("taxation", 0.0) > 0.0, (state.record.income, rich.record.outlays))
state.receive_revenue(world)
check("income already assessed is not assessed again", abs(state.money - 0.1 * 3.0e6) < 1e-6, state.money)
rich.record.income["edge:economy"] += 1.0e6
state.receive_revenue(world)
check("a year's new income is assessed", abs(state.money - (0.1 * 3.0e6 + 0.1 * 1.0e6)) < 1e-6, state.money)

# a body that holds nothing pays nothing: no purse goes into debt to the state
world = make_world()
world.forms = [dict(LEVY, rate=1.0)]
world.strata[1].money = 0.0
world.state.receive_revenue(world)
check("a levy is no more than the purse can pay", all(body.money >= 0.0 for body in world.strata)
      and world.strata[1].money == 0.0, [body.money for body in world.strata])

# a form can be asked of named bodies only
world = make_world()
world.forms = [dict(LEVY, from_strata=["rich"])]
only = revenue.assess(world)[0]
check("a form that names its payers takes from those bodies only",
      [payer.record.stratum for payer, _ in only.payers] == ["rich"], only.payers)

# ---- a surplus beyond the reserve relieves the hunger of the strata, then buys works ------------------
world = make_world(money=1.0e9)
state, poor = world.state, world.strata[1]
hunger = poor.record.members * (world.food_cost * 0.5 + world.housing_cost * 0.5)
state.relieve_strata(1.0e9, world)
check("relief is paid to the body that reports its need unmet, to the extent of that need",
      abs(poor.money - (1.0e6 + hunger)) < 1e-6 and abs(state.money - (1.0e9 - hunger)) < 1e-6, (poor.money, state.money))
check("a body that is not hungry is given nothing", world.strata[0].money == 5.0e6, world.strata[0].money)
check("relief is booked as an outlay of the state", abs(state.record.outlays.get("relief", 0.0) - hunger) < 1e-6,
      state.record.outlays)
world = make_world(money=1.0e9)
world.state.relieve_strata(hunger / 4.0, world)
check("relief is no more than the surplus", abs(world.state.record.outlays.get("relief", 0.0) - hunger / 4.0) < 1e-6,
      world.state.record.outlays)

# ---- end to end on a played start --------------------------------------------------------------------
def one_year(game):
	game.state.scenario.year += 1
	game.advance_actors(game.state.scenario.year)


game = sim()
game.civ["state_revenue"] = list(game.civ["state_revenue"]) + [dict(LEVY, rate=0.01)]
treasury = game.state_treasury()
for _year in range(3):
	one_year(game)
home_strata = [body for body in game.actors.of_kind("stratum") if body.record.country is None]
check("the home state's strata are the ones it taxes", home_strata and all(
      body.record.outlays.get("taxation", 0.0) > 0.0 for body in home_strata if body.record.stratum != "bonded"
      and body.record.income.get("edge:economy", 0.0) > 0.0 and body.record.stratum != "poor"),
      [(body.record.stratum, body.record.outlays) for body in home_strata])
check("a foreign country's strata pay the home state nothing", all(
      body.record.outlays.get("taxation", 0.0) == 0.0 for body in game.actors.of_kind("stratum")
      if body.record.country is not None), "foreign strata taxed")
check("the levy is a form of revenue the state reports", treasury.record.revenue_by_form.get("income_levy", 0.0) > 0.0,
      treasury.record.revenue_by_form)
