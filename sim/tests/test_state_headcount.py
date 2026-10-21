"""Complaint 602: a state's wanted headcount is drawn from its own country's working-age people and the food that
feeds them; the shortfall is reported with a cause, and a feasible army is untouched."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import headcount
from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, seed_cast
from sim.agents.country_hands import hands_of
from sim.agents.country_population import step_country

from .country_state_world import StateWorld

# the pure ledger
hands = headcount.Hands(working_age=1000.0, farm_hands=600.0, food_ratio=1.0)
feasible = headcount.fit(300.0, hands, claimed_elsewhere=50.0)
check("a feasible army is untouched", feasible.granted == 300.0 and feasible.shortfall == 0.0 and feasible.cause is None, feasible)
over_people = headcount.fit(5000.0, hands)
check("an army larger than the working age gets at most the free working-age people, with the cause",
	  over_people.granted <= 400.0 and over_people.cause == headcount.WORKING_AGE and over_people.shortfall > 0.0, over_people)
over_farms = headcount.fit(500.0, hands)
check("an army that would strip the farms is cut to the hands the farms can spare",
	  over_farms.granted == 400.0 and over_farms.cause == headcount.FARM_HANDS, over_farms)
hungry = headcount.fit(300.0, headcount.Hands(1000.0, 600.0, 0.5))
check("a country whose food fell short keeps a smaller army, caused by food",
	  hungry.granted == 200.0 and hungry.cause == headcount.FOOD, hungry)
check("other state people are taken from the same pool", headcount.fit(300.0, hands, 150.0).granted == 250.0)
check("with no account of the country's hands the wish stands", headcount.fit(300.0, None).granted == 300.0)


# a foreign country with a declared army
class CountryAnswers:
	def pay_per_person_year(self, trade):
		return 10.0

	def society_output(self):
		return 1.0e6

	def price_per_tonne(self, material):
		return 2.0

	def coin_regime(self):
		return "commodity"

	def coin_stock_value(self):
		return 0.0

	def need_floor_costs_per_person_year(self):
		return {"food": 5.0}


class Shared(StateWorld):
	def country_economy(self, country):
		return CountryAnswers()

	def population_total(self):
		return 1000.0


def government_of(standing_army):
	registry = ActorRegistry(ActorsState(home_country="home"))
	profile = CountryProfile(country="far", population=100000.0, extra={"standing_army": standing_army})
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0e9)
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home", population=1000.0), "far": profile})
	profile = registry.state.countries["far"]
	for _ in range(3):
		step_country(profile, weather_multiplier=1.0)
	government = registry.actors["government:far"]
	return profile, government, CountryWorld(Shared(), profile, registry)


profile, government, world = government_of(1.0e7)
people = hands_of(profile)
check("a foreign country's hands are its own working age", people.working_age == profile.cohorts["working_age"], people)
government.record.army = 1.0e7
government.pay_standing_need(world)
booked = government.record.headcount["army"]
check("a foreign army larger than its working age disbands to the people free to serve",
	  government.record.army <= people.working_age - people.farm_hands + 1e-6, (government.record.army, people))
check("the shortfall is reported with a cause", booked["shortfall"] > 0.0 and booked["cause"] == headcount.WORKING_AGE, booked)

profile, government, world = government_of(10.0)
government.pay_standing_need(world)
check("a feasible foreign army is untouched",
	  government.record.headcount["army"]["shortfall"] == 0.0 and government.record.army == 10.0, government.record.headcount)

profile, government, world = government_of(100.0)
free = hands_of(profile).working_age - hands_of(profile).farm_hands
profile.farm["shortfall_kg"] = 1.0e12
famine = hands_of(profile)
check("a famine year is read from the country's farm", famine.food_ratio < 0.01, famine)
government.record.army = free
government.pay_standing_need(world)
check("a state whose food falls short cannot keep its full army", government.record.army < free * 0.5 + 1e-6, (government.record.army, free))
