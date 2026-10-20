"""A foreign country runs the disease model the home country runs: an infection seeded abroad raises that country's deaths, mortality enters its Population, and the pathogen can cross to another country by contact."""

QUICK_TOPIC = False

import time

from .harness import check

from sim.agents.api import ActorRegistry, ActorsState, CountryProfile, strata_spawner
from sim.agents.country_disease import introduce
from sim.agents.country_population import people_counted

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


def build(names=("far", "other"), exposure=None):
	state = ActorsState(home_country="home")
	state.countries["home"] = CountryProfile(country="home", population=1000.0, strata=DEFINITIONS)
	for name in names:
		state.countries[name] = CountryProfile(country=name, population=200000.0, strata=DEFINITIONS)
	if exposure:
		state.countries["far"].extra["disease_exposure"] = exposure
	return ActorRegistry(state)


def years(registry, count, world=None):
	world = world or PopulationWorld()
	for _ in range(count):
		strata_spawner(registry, world)
		world.year += 1


def deaths_of(profile):
	return sum(profile.disease_deaths.values())


# a seeded infection abroad raises that country's deaths and leaves another country's unchanged
plain = build()
years(plain, 2)
seeded = build()
years(seeded, 1)
introduce(seeded.state.countries["far"], "smallpox")
years(seeded, 1)
check("an infection seeded in a foreign country kills people there", deaths_of(seeded.state.countries["far"]) > 0,
	  seeded.state.countries["far"].disease_deaths)
check("the pathogen's arrival is recorded", seeded.state.countries["far"].disease_introduced.get("smallpox"))
check("the seeded country has fewer people than the same country with no infection",
	  people_counted(seeded.state.countries["far"]) < people_counted(plain.state.countries["far"]),
	  (people_counted(seeded.state.countries["far"]), people_counted(plain.state.countries["far"])))
check("another country's people are unchanged in the year of the seeding",
	  people_counted(seeded.state.countries["other"]) == people_counted(plain.state.countries["other"]))
check("another country has no deaths from it yet", deaths_of(seeded.state.countries["other"]) == 0)
check("a country with no infection pays nothing for the model", not plain.state.countries["far"].disease_records)

# contact between countries: the pathogen reaches a neighbour that has none
spread = build()
years(spread, 1)
introduce(spread.state.countries["far"], "smallpox")
years(spread, 40)
check("a pathogen circulating in one foreign country reaches another by contact",
	  deaths_of(spread.state.countries["other"]) > 0, spread.state.countries["other"].disease_introduced)

# the same contact windows as the home country, read from the profile's exposure
windowed = build(names=("far", "other"), exposure={"outside_contact": [{"pathogens": ["smallpox"], "years": [100, 200], "circulating": True}]})
years(windowed, 40)
check("a country whose civilisation lists outside contact is reached by it",
	  windowed.state.countries["far"].disease_introduced.get("smallpox"), windowed.state.countries["far"].disease_introduced)

# the model is deterministic for one world and the cost is small
again = build()
years(again, 1)
introduce(again.state.countries["far"], "smallpox")
years(again, 1)
check("the same world and seeding give the same deaths", again.state.countries["far"].disease_deaths == seeded.state.countries["far"].disease_deaths)
quiet = build()
start = time.process_time()
years(quiet, 100)
check("a hundred quiet years of two foreign countries is cheap", time.process_time() - start < 5.0, time.process_time() - start)
