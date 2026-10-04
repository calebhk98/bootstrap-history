"""Strata: bodies of people as actors. Seeding from data, needs, growth, schooling, mobility, keep."""
from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CountryProfile
from sim.agents import registry as registry_module
from sim.agents.strata_seed import seed_strata, strata_definitions, strata_spawner
from sim.agents.stratum import Stratum

from .agents_fake_world import FakeWorld, make_node


class StrataWorld(FakeWorld):
	"""A world that prices a food basket, housing, wages, and may report observed figures."""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.food = 100.0
		self.housing = 40.0
		self.pay = {"labourer": 150.0, "artisan": 400.0, "merchant": 900.0}
		self.observed = {}

	def subsistence_cost_per_person_year(self):
		return self.food

	def housing_cost_per_person_year(self):
		return self.housing

	def pay_per_person_year(self, trade):
		return self.pay[trade]

	def observed_stratum(self, country, name):
		return self.observed.get((country, name))


def edge_net(actors):
	"""Money that crossed the edge of the modelled actors: in less out, by the books."""
	total = 0.0
	for actor in actors:
		total += sum(value for label, value in actor.record.income.items() if label.startswith("edge:"))
		total -= sum(value for label, value in actor.record.outlays.items() if label.startswith("edge:"))
	return total


def build(definitions, population=100000.0, **profile_fields):
	state = ActorsState(home_country="home")
	state.countries["home"] = CountryProfile(country="home", population=population, strata=definitions,
											 **profile_fields)
	registry = ActorRegistry(state)
	strata_spawner(registry, StrataWorld())
	return registry


def stratum(registry, name, country="home"):
	return registry.actors["stratum:%s:%s" % (country, name)]


# ---- seeding from a data list ------------------------------------------------------------
DEFINITIONS = [{"name": "toilers", "share": 0.7, "trade": "labourer", "literacy": 0.1},
			   {"name": "owners", "share": 0.01, "property_share": 0.3, "literacy": 0.9}]
registry = build(DEFINITIONS)
toilers = stratum(registry, "toilers")
check("a stratum is an actor of kind stratum with an id from country and name",
	  isinstance(toilers, Stratum) and toilers.record.kind == "stratum" and toilers.actor_id == "stratum:home:toilers")
check("members are share times population", abs(toilers.record.members - 70000.0) < 1e-6, toilers.record.members)
check("literacy comes from the data", toilers.record.literacy == 0.1 and stratum(registry, "owners").record.literacy == 0.9)
check("the home country's strata carry country None", toilers.record.country is None)
check("a stratum starts with no research tree", not toilers.knowledge and not toilers.works)
again = seed_strata(registry, StrataWorld())
check("seeding twice founds nothing more", again == [] and len(registry.of_kind("stratum")) == 2, again)
check("the strata spawner is registered", "strata" in [name for name, _spawner in registry_module.SPAWNERS])

state = ActorsState(home_country="home")
state.countries["home"] = CountryProfile(country="home", population=1000.0, strata=DEFINITIONS)
state.countries["far"] = CountryProfile(country="far", population=2000.0, strata=DEFINITIONS)
registry_two = ActorRegistry(state)
founded = seed_strata(registry_two, StrataWorld())
far = stratum(registry_two, "toilers", "far")
check("every country in the state gets its strata, foreign ones with their country",
	  len(founded) == 4 and far.record.country == "far" and abs(far.record.members - 1400.0) < 1e-6, founded)

# ---- a default derived from what the profile states ---------------------------------------
profile = CountryProfile(country="home", population=1000000.0, urban_fraction=0.2, literacy_general=0.1,
						 literacy_elite=0.9, extra={"debt_bondage": True})
definitions = strata_definitions(profile)
names = {entry["name"] for entry in definitions}
check("the default has several bodies of people", len(definitions) >= 4, names)
check("default shares add up to the whole population", abs(sum(entry["share"] for entry in definitions) - 1.0) < 1e-9,
	  sum(entry["share"] for entry in definitions))
check("debt bondage in the profile gives a bonded stratum with an owner who exists",
	  any(entry.get("bonded") and entry.get("owner") in names for entry in definitions))
check("without bondage there is no bonded stratum",
	  not any(entry.get("bonded") for entry in strata_definitions(CountryProfile(population=10.0, urban_fraction=0.1))))
check("rises_to and falls_to name strata that exist",
	  all(entry.get(key) in names for entry in definitions for key in ("rises_to", "falls_to") if entry.get(key)))
check("the elite are as literate as the data says", max(entry["literacy"] for entry in definitions) == 0.9)
check("a profile's own list is used as given", strata_definitions(CountryProfile(strata=DEFINITIONS)) == DEFINITIONS)
registry_default = ActorRegistry(ActorsState(home_country="home"))
registry_default.state.countries["home"] = profile
seed_strata(registry_default, StrataWorld())
check("a default-seeded country holds its whole population",
	  abs(sum(actor.record.members for actor in registry_default.of_kind("stratum")) - 1000000.0) < 1e-3)

# ---- a well-paid stratum grows, learns, and some members rise ------------------------------
definitions = [{"name": "artisans", "share": 0.5, "trade": "artisan", "literacy": 0.5, "rises_to": "merchants",
				"work_share": 1.0},
			   {"name": "merchants", "share": 0.5, "trade": "merchant", "literacy": 0.5}]
registry = build(definitions)
world = StrataWorld()
artisans, merchants = stratum(registry, "artisans"), stratum(registry, "merchants")
people_before = (artisans.record.members, merchants.record.members)
literacy_before = artisans.record.literacy
registry.advance(world)
grown = [people * (1.0 + actor.record.last_growth) for people, actor in zip(people_before, (artisans, merchants))]
check("a well-paid stratum grows", artisans.record.last_growth > 0 and artisans.record.welfare > 2.0,
	  (artisans.record.last_growth, artisans.record.welfare))
check("a well-paid stratum gains literacy", artisans.record.literacy > literacy_before, artisans.record.literacy)
check("some members of a literate, comfortable stratum rise",
	  artisans.record.members < grown[0] - 1.0 and merchants.record.members > grown[1] + 1.0,
	  (artisans.record.members, grown))
check("food is fully met when pay allows", artisans.record.shortfall.get("food", 1.0) == 0.0, artisans.record.shortfall)
check("savings build up for the comfortable", artisans.money > 0, artisans.money)

# ---- a starving stratum shrinks and records its food shortfall -----------------------------
registry = build([{"name": "poor", "share": 1.0, "trade": "labourer", "literacy": 0.05, "work_share": 0.2}])
world = StrataWorld()
poor = stratum(registry, "poor")
start = poor.record.members
for _year in range(3):
	registry.advance(world)
check("a starving stratum records an unmet share of food", 0.0 < poor.record.shortfall["food"] <= 1.0, poor.record.shortfall)
check("a starving stratum shrinks", poor.record.members < start and poor.record.last_growth < 0, poor.record.last_growth)
check("housing goes unmet before food is touched, and goods first of all",
	  poor.record.shortfall["housing"] >= poor.record.shortfall["food"] and poor.record.shortfall["goods"] == 1.0,
	  poor.record.shortfall)
check("literacy falls when nothing funds schooling", poor.record.literacy < 0.05, poor.record.literacy)

# ---- bonded strata cost their owner -------------------------------------------------------
definitions = [{"name": "masters", "share": 0.1, "property_share": 0.5, "literacy": 0.8},
			   {"name": "bondsmen", "share": 0.9, "bonded": True, "owner": "masters", "literacy": 0.0}]
registry = build(definitions)
world = StrataWorld()
masters, bondsmen = stratum(registry, "masters"), stratum(registry, "bondsmen")
check("seeding hands the bonded their keep from the owner", bondsmen.money > 0, bondsmen.money)
check("the owner's purse fell by exactly what the bonded one holds", abs(masters.money + bondsmen.money) < 1e-6,
	  (masters.money, bondsmen.money))
check("the keep is the food basket for every bonded member",
	  abs(bondsmen.money - bondsmen.record.members * world.food) < 1e-6, bondsmen.money)
registry.advance(world)
check("the bonded earn nothing of their own", "edge:economy" not in bondsmen.record.income, bondsmen.record.income)
check("the bonded eat from the keep: no food shortfall", bondsmen.record.shortfall["food"] == 0.0, bondsmen.record.shortfall)
paid = bondsmen.record.income.get("keep of bonded", 0.0)
check("what leaves the owner is exactly what reaches the bonded",
	  paid > 0 and abs(masters.record.outlays.get("keep of bonded", 0.0) - paid) < 1e-6, paid)
check("bonded members grow more slowly than a free stratum with food met", bondsmen.record.last_growth < 0.01,
	  bondsmen.record.last_growth)

# ---- headcount and money are conserved -----------------------------------------------------
definitions = [{"name": "low", "share": 0.4, "trade": "labourer", "literacy": 0.6, "rises_to": "high", "work_share": 1.0},
			   {"name": "high", "share": 0.2, "trade": "merchant", "literacy": 0.9, "falls_to": "low"},
			   {"name": "owners", "share": 0.4, "property_share": 0.2, "literacy": 0.9}]
registry = build(definitions)
world = StrataWorld()
actors = registry.of_kind("stratum")
money_before = sum(actor.money for actor in actors)
edge_before = edge_net(actors)
people_before = {actor.actor_id: actor.record.members for actor in actors}
registry.advance(world)
grown = {actor.actor_id: people_before[actor.actor_id] * (1.0 + actor.record.last_growth) for actor in actors}
check("headcount is conserved across mobility apart from births and deaths",
	  abs(sum(actor.record.members for actor in actors) - sum(grown.values())) < 1e-6)
check("mobility actually moved people",
	  any(abs(actor.record.members - grown[actor.actor_id]) > 1.0 for actor in actors))
check("money is conserved apart from edge flows",
	  abs(sum(actor.money for actor in actors) - money_before - (edge_net(actors) - edge_before)) < 1e-6)
check("nothing is left pending after the year", all(not actor.record.moving for actor in actors))

# ---- observed figures override the stratum's own books -------------------------------------
registry = build([{"name": "toilers", "share": 1.0, "trade": "labourer", "literacy": 0.1}], population=1000.0)
world = StrataWorld()
world.observed[(None, "toilers")] = {"members": 5000.0, "income": 1.0e6}
toilers = stratum(registry, "toilers")
registry.advance(world)
check("observed headcount replaces the stratum's own", toilers.record.members == 5000.0, toilers.record.members)
check("observed income replaces the wage computation",
	  abs(toilers.record.income.get("edge:economy", 0.0) - 1.0e6) < 1e-6, toilers.record.income)
check("welfare follows the observed figures", abs(toilers.record.welfare - 1.0e6 / 5000.0 / world.food) < 1e-9,
	  toilers.record.welfare)


# ---- determinism and no research ----------------------------------------------------------
def run_once():
	registry = build(DEFINITIONS)
	world = StrataWorld()
	for _year in range(4):
		registry.advance(world)
	return [(actor.actor_id, actor.record.members, actor.money, actor.record.literacy)
			for actor in registry.of_kind("stratum")]


check("two runs from the same start agree exactly", run_once() == run_once())

registry = build(DEFINITIONS)
world = StrataWorld()
world.nodes["plough"] = make_node("plough", revenue=100.0)
world.demonstrated_nodes.add("plough")
world.public_nodes.add("plough")
toilers = stratum(registry, "toilers")
toilers.credit(1.0e9, "test")
for _year in range(3):
	registry.advance(world)
check("a stratum never researches or copies",
	  not toilers.knowledge and not toilers.works and not toilers.workforce
	  and toilers.imitation_candidates(world) == [] and toilers.consider_imitation(world) == [])

# ---- people with land of their own eat from it when wages fall short ------------------------
plot_world = StrataWorld()
plot_world.pay = {"labourer": 1.0}
plot_registry = ActorRegistry(ActorsState(home_country="home"))
landed = plot_registry.add("stratum:home:farmers", ActorRecord(kind="stratum", stratum="farmers", members=1000.0,
	plan={"name": "farmers", "trade": "labourer", "own_plot": True}))
landless = plot_registry.add("stratum:home:poor", ActorRecord(kind="stratum", stratum="poor", members=1000.0,
	plan={"name": "poor", "trade": "labourer"}))
landed.advance(plot_world)
landless.advance(plot_world)
check("people with their own plot are fed when wages are below subsistence",
	  landed.record.shortfall.get("food") == 0.0, landed.record.shortfall)
check("people without land go hungry at the same wage", landless.record.shortfall.get("food", 0.0) > 0.0,
	  landless.record.shortfall)
