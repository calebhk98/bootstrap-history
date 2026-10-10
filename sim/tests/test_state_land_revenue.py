"""Complaint 315: a state can tax the rent the land market lets land at (`land_rent`) and the land's capital
value, the rent capitalised at the market rate (`land_value`); a form on either is collected from the owners'
purses through the ledger, so no money appears."""
from .harness import *  # noqa: F401,F403
from types import SimpleNamespace

from sim.agents import revenue
from sim.agents.api import Government, Stratum, stratum_id
from sim.agents.records import ActorRecord
from sim.economy import land_rents
from sim.tests.agents_fake_world import FakeWorld

QUICK_TOPIC = True


class LandWorld(FakeWorld):
	"""A world that answers what the land bases ask: rent paid per tile, who receives it, the market rate."""

	def __init__(self, rents, owners, rate=0.05):
		super().__init__()
		self.rents, self.owners, self.rate, self.forms = rents, owners, rate, []
		self.state = Government("government:home", ActorRecord(kind="government", money=0.0))

	def revenue_forms(self):
		return self.forms

	def government(self):
		return self.state

	def land_rent_paid_by_tile(self):
		return dict(self.rents)

	def land_rent_owners(self):
		return list(self.owners)

	def market_rate(self):
		return self.rate

	def revenue_assessments(self):
		return revenue.assess(self)


def owner(name, money):
	return Stratum(stratum_id("home", name), ActorRecord(kind="stratum", stratum=name, members=10.0, money=money))


def producer(tile, recipe, runs):
	return SimpleNamespace(tile=tile, recipe_id=recipe, last_runs=runs)


# ---- rent paid on land let, per tile, from the economy's records ---------------------------------
setup = SimpleNamespace(land_per_run={"farm": 2.0, "mine": 0.0})
record = SimpleNamespace(land_rent={"a": 10.0, "b": 4.0, "c": 7.0}, producers={
	"p1": producer("a", "farm", 5.0), "p2": producer("a", "farm", 1.0), "p3": producer("b", "farm", -1.0),
	"p4": producer("c", "mine", 9.0)})
paid = land_rents.rent_paid_by_tile(setup, record)
check("rent paid on a tile is its rent per hectare times the hectares its producers worked last year",
      paid == {"a": 10.0 * 2.0 * 6.0}, paid)
check("a tile where nothing was let pays no rent, and a recipe that takes no land is none",
      "b" not in paid and "c" not in paid, paid)

# ---- the basis ------------------------------------------------------------------------------------
LAND_RENT = {"form": "rent_levy", "basis": "land_rent", "rate": 0.25}
LAND_VALUE = {"form": "land_tax", "basis": "land_value", "rate": 0.01}
world = LandWorld({"a": 120.0, "b": 80.0}, [])
world.forms = [LAND_RENT, LAND_VALUE]
by_form = {assessed.form: assessed for assessed in revenue.assess(world)}
check("a land_rent form is its rate times all the rent paid", abs(by_form["rent_levy"].money - 0.25 * 200.0) < 1e-9,
      by_form["rent_levy"])
check("land is worth its rent capitalised at the market rate", abs(by_form["land_tax"].base - 200.0 / 0.05) < 1e-9,
      by_form["land_tax"])
check("a form on land value is its rate times that value", abs(by_form["land_tax"].money - 0.01 * 4000.0) < 1e-9,
      by_form["land_tax"])
world.rate = 0.0
check("with no market rate there is no capital value to tax",
      {assessed.form: assessed.money for assessed in revenue.assess(world)}["land_tax"] == 0.0, world.rate)

# ---- collected from the owners' purses through the ledger ----------------------------------------
rich, middling = owner("rich", 1000.0), owner("middling", 5.0)
world = LandWorld({"a": 120.0, "b": 80.0}, [(rich, 150.0), (middling, 50.0)])
world.forms = [dict(LAND_RENT, rate=0.1)]
before = world.state.money + rich.money + middling.money
world.state.receive_revenue(world)
check("the state received a share of each owner's rent", abs(world.state.money - (15.0 + 5.0)) < 1e-9, world.state.money)
check("owners lost what the state gained", abs(rich.money - 985.0) < 1e-9 and abs(middling.money) < 1e-9,
      (rich.money, middling.money))
check("no money appeared", abs(world.state.money + rich.money + middling.money - before) < 1e-9, world.state.money)
check("the tax is booked as taxation", world.state.record.income.get("taxation", 0.0) > 0.0, world.state.record.income)
world = LandWorld({"a": 120.0}, [(rich, 100.0)])
world.forms = [dict(LAND_RENT, rate=1.0, from_strata=["middling"])]
check("a form can name the owners it falls on", revenue.assess(world)[0].money == 0.0, revenue.assess(world))
