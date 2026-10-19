"""A foreign country feeds itself: its farm, granary and harvest are the home country's agriculture model, sized from its own land and people, so its food supply and its deaths are outcomes of land and weather."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import CountryProfile
from sim.agents.country_farm import farm_state
from sim.agents.country_population import people_counted, step_country
from sim.world import agriculture

PEOPLE = 200000.0
YEARS = 30


def country(name, arable_hectares=None):
	extra = {} if arable_hectares is None else {"arable_hectares": arable_hectares}
	return CountryProfile(country=name, population=PEOPLE, extra=extra)


def run(profile, years, weather=None):
	"""Step the country; the flows of the last year."""
	flows = None
	for _ in range(years):
		flows = step_country(profile, weather_multiplier=weather)
	return flows


# the land that feeds the seeded people at reference technique
ample = agriculture.farmland_for_population(PEOPLE * 0.75).hectares

# 1. less arable land feeds fewer people
rich, poor = country("rich", ample * 2), country("poor", ample * 0.5)
run(rich, YEARS, 1.0)
run(poor, YEARS, 1.0)
check("a country with less arable land feeds fewer people",
	  people_counted(poor) < people_counted(rich), (people_counted(poor), people_counted(rich)))
check("its food supply is the harvest of its land, not a fixed multiple of its need",
	  farm_state(poor)["hectares"] < farm_state(rich)["hectares"], (farm_state(poor), farm_state(rich)))

# 2. a failed harvest raises the shortfall and the deaths against a twin with a good one
good, bad = country("twin", ample), country("twin", ample)
run(good, 5, 1.0)
run(bad, 5, 1.0)
good_flows = run(good, 1, 1.0)
bad_flows = run(bad, 1, agriculture.WEATHER_FLOOR_MULTIPLIER)
check("a failed harvest leaves a food shortfall a good one does not",
	  farm_state(bad)["shortfall_kg"] > farm_state(good)["shortfall_kg"] == 0.0,
	  (farm_state(bad)["shortfall_kg"], farm_state(good)["shortfall_kg"]))
check("a failed harvest raises the country's deaths over its twin's", bad_flows.deaths > good_flows.deaths,
	  (bad_flows.deaths, good_flows.deaths))

# 3. the farm state lives on the profile, so it saves with it
check("the farm state is on the profile, so it round-trips with it", "stock_kg" in farm_state(good), farm_state(good))
