"""A foreign country's people are one Population stepped by the home country's code; its strata follow the people counted."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRegistry, ActorsState, CountryProfile, CountryWorld, strata_spawner
from sim.agents.country_population import people_counted
from sim.world import demography

from .agents_fake_world import FakeWorld

DEFINITIONS = [{"name": "toilers", "share": 0.7, "trade": "labourer", "literacy": 0.1},
			   {"name": "owners", "share": 0.3, "property_share": 0.3, "literacy": 0.9}]


class PopulationWorld(FakeWorld):
	def population_total(self):
		return 1000.0

	def subsistence_cost_per_person_year(self):
		return 100.0

	def need_floor_costs_per_person_year(self):
		return {"food": 100.0}

	def pay_per_person_year(self, trade):
		return 150.0

	def observed_stratum(self, country, name):
		return None


def build():
	state = ActorsState(home_country="home")
	state.countries["home"] = CountryProfile(country="home", population=1000.0, strata=DEFINITIONS)
	state.countries["far"] = CountryProfile(country="far", population=200000.0, strata=DEFINITIONS)
	return ActorRegistry(state)


def foreign_members(registry):
	return sum(actor.record.members for actor in registry.of_kind("stratum") if actor.record.country == "far")


def years(registry, count):
	world = PopulationWorld()
	for _ in range(count):
		strata_spawner(registry, world)


registry = build()
far = registry.state.countries["far"]
years(registry, 1)
seeded = people_counted(far)
check("a foreign country's people are counted from its cohorts once stepped, near the seeded figure",
	  abs(seeded - 200000.0) < 0.1 * 200000.0, seeded)
years(registry, 40)
grown = people_counted(far)
check("a foreign country's population changes over a run with no hand assignment", grown != seeded, (seeded, grown))
check("its cohorts are the three age bands of one Population", set(far.cohorts) == {"children", "working_age", "elderly"}, far.cohorts)
check("its strata sum to the people counted there", abs(foreign_members(registry) - grown) < 1e-6 * grown, (foreign_members(registry), grown))
check("CountryWorld answers the people counted, not the seeded figure",
	  CountryWorld(PopulationWorld(), far, registry).population_total() == grown)
check("the home country's strata follow the world's count as before",
	  abs(sum(actor.record.members for actor in registry.of_kind("stratum") if actor.record.country is None) - 1000.0) < 1e-6)

registry = build()
years(registry, 1)
before = people_counted(registry.state.countries["far"])
saved = demography.ANNUAL_FERTILITY_RATE_PER_WOMAN
demography.ANNUAL_FERTILITY_RATE_PER_WOMAN = 0.0
try:
	years(registry, 30)
finally:
	demography.ANNUAL_FERTILITY_RATE_PER_WOMAN = saved
after = people_counted(registry.state.countries["far"])
check("a country whose births are removed declines", after < 0.9 * before, (before, after))
check("and its strata decline with it", abs(foreign_members(registry) - after) < 1e-6 * max(after, 1.0), (foreign_members(registry), after))

# the fixed supply the country is fed from bounds its growth
registry = build()
years(registry, 60)
first = people_counted(registry.state.countries["far"])
years(registry, 60)
check("a foreign population stays bounded by the supply it is fed from",
	  people_counted(registry.state.countries["far"]) < 3.0 * first, (first, people_counted(registry.state.countries["far"])))
