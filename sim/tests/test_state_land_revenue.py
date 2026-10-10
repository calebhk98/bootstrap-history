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
		self.tile_owners = []  # (tile, owner, rent received from that tile)
		self.arable = {tile: 1.0 for tile in rents}
		self.state = Government("government:home", ActorRecord(kind="government", money=0.0))

	def revenue_forms(self):
		return self.forms

	def government(self):
		return self.state

	def land_rent_paid_by_tile(self):
		return dict(self.rents)

	def land_rent_owners(self, tiles=None):
		if tiles is None:
			return list(self.owners)
		return [(who, rent) for tile, who, rent in self.tile_owners if tile in tiles]

	def held_tiles(self):
		return sorted(self.rents)

	def arable_share(self, tiles):
		return sum(self.arable[tile] for tile in tiles) / sum(self.arable.values())

	def harvest_tonnes(self):
		return 1000.0

	def material_price(self, material):
		return 2.0

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


# ---- rent goes to the owners that received it: cohorts keep it, strata are slices of them ----------------
cohort_a = SimpleNamespace(agent_id="household:a:0", tile="a", ownership_share=1.0)
cohort_b = SimpleNamespace(agent_id="household:a:1", tile="a", ownership_share=3.0)
cohort_c = SimpleNamespace(agent_id="household:b:0", tile="b", ownership_share=1.0)
rent_record = SimpleNamespace(land_rent={"a": 10.0, "b": 5.0}, producers={
	"p1": producer("a", "farm", 2.0), "p2": producer("b", "farm", 1.0)},
	cohorts={cohort.agent_id: cohort for cohort in (cohort_a, cohort_b, cohort_c)})
received = land_rents.rent_received_by_cohort(SimpleNamespace(land_per_run={"farm": 1.0}), rent_record)
check("the rent paid on a tile is shared among its cohorts by what each owns",
      received == {"household:a:0": 5.0, "household:a:1": 15.0, "household:b:0": 5.0}, received)
only_b = land_rents.rent_received_by_cohort(SimpleNamespace(land_per_run={"farm": 1.0}), rent_record, frozenset({"b"}))
check("limited to tiles, only those tiles' cohorts receive rent", only_b == {"household:b:0": 5.0}, only_b)

from sim.engine.agents_port_revenue import RevenueView


class StubSim:
	"""Only what `land_rent_owners` reads: the cohorts' rent curve and the home strata."""

	def __init__(self, curve, strata):
		self.economy = SimpleNamespace(agent_cohort_land_rents=lambda tiles=None: curve)
		self.actors = SimpleNamespace(of_kind=lambda kind: strata)


class StubView(RevenueView):
	def __init__(self, sim):
		self._sim = sim

	def pay_per_person_year(self, trade):
		return 1.0

	def society_output(self):
		return 0.0


poor = owner("poor", 0.0)
rich_stratum = owner("rich", 0.0)
exited = owner("gone", 0.0)
exited.record.exited_year = 5
view = StubView(StubSim([(10.0, 0.0), (10.0, 40.0)], [poor, rich_stratum, exited]))
owners = view.land_rent_owners()
check("the strata, as slices of the cohorts, are the named owners of the rent of their slice",
      [(who.record.stratum, rent) for who, rent in owners] == [("rich", 40.0)], owners)
check("a stratum that exited owns nothing", all(who is not exited for who, _rent in owners), owners)
check("the economy still opening names no owner",
      StubView(StubSim(None, [poor])).land_rent_owners() == [], "opening")

# ---- two revenue forms stacked on one land would count it twice, so a form names its provinces --------
TITHE = {"form": "tithe", "basis": "harvest", "rate": 0.1}
PROPERTY = {"form": "property_tribute", "basis": "land_value", "rate": 0.01}
world = LandWorld({"sicily": 100.0, "syria": 50.0}, [])
world.arable = {"sicily": 3.0, "syria": 1.0}
world.forms = [dict(TITHE, except_tiles=["syria"]), dict(PROPERTY, tiles=["syria"])]
by_form = {assessed.form: assessed for assessed in revenue.assess(world)}
check("a form can be levied on every held tile but those it excepts: the crop taxed is those tiles' share",
      abs(by_form["tithe"].base - 1000.0 * 2.0 * 0.75) < 1e-9, by_form["tithe"])
check("a form on named tiles reads the rent of those tiles only",
      abs(by_form["property_tribute"].base - 50.0 / 0.05) < 1e-9, by_form["property_tribute"])
world.forms = [dict(TITHE, tiles=["sicily"]), dict(PROPERTY, except_tiles=["sicily"])]
check("the two forms together tax each tile once",
      abs(sum(assessed.base for assessed in revenue.assess(world)) - (1000.0 * 2.0 * 0.75 + 1000.0)) < 1e-9, world.forms)
world.forms = [{"form": "poll", "basis": "adult_labour_years", "rate": 0.1, "tiles": ["syria"]}]
try:
	revenue.assess(world)
	refused = False
except ValueError:
	refused = True
check("a national basis cannot be limited to tiles", refused)
world = LandWorld({"sicily": 100.0, "syria": 50.0}, [])
world.tile_owners = [("sicily", rich, 100.0), ("syria", middling, 50.0)]
world.forms = [dict(PROPERTY, rate=1.0, tiles=["syria"])]
payers = revenue.assess(world)[0].payers
check("a form on named tiles falls on the owners of the rent of those tiles",
      [who for who, _owed in payers] == [middling], payers)

# ---- Rome's own file: a tithe in some provinces, assessed property in others, never both ---------------
import json
import os
with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "civilizations", "rome_100ad.json")) as handle:
	rome = json.load(handle)
forms = {declared["form"]: declared for declared in rome["state_revenue"]}
property_form = forms["property_tribute"]
tithe_form = forms["land_tax"]
check("Rome assesses property in the provinces it names", property_form["basis"] == "land_value" and property_form["tiles"], property_form)
check("the tithe is levied everywhere else", set(tithe_form["except_tiles"]) == set(property_form["tiles"]), tithe_form)
check("the property provinces are tiles Rome holds", set(property_form["tiles"]) <= set(rome["home_tiles"]), property_form)
check("both land forms cite a source", all(forms[name]["_internal"]["source"] for name in ("land_tax", "property_tribute")))
