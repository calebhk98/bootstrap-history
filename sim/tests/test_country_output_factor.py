"""Complaint 649: what a plant abroad takes is cut by the war and aftermath its own country's hazards date, never by the
home country's. The rules are called on built inputs and a stand-in world."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import country_hazards
from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, seed_cast
from sim.agents.business_plant_books import books_at_country_prices
from sim.agents.country_state_site import gross_at_country_prices

from .country_state_world import StateWorld

HAZARDS = [{"name": "raids", "years": [90, 110], "sack_chance": 0.2},
		   {"name": "war", "years": [95, 105], "output_factor": 0.6},
		   {"name": "famine", "years": [100, 100], "output_factor": 0.8},
		   {"name": "later war", "years": [200, 210], "output_factor": 0.1}]

check("no hazard running leaves the output whole", country_hazards.output_factor(HAZARDS, 50) == 1.0 and country_hazards.output_factor([], 100) == 1.0)
check("a hazard with no output factor takes none of it", country_hazards.output_factor(HAZARDS, 92) == 1.0)
check("a war running takes its factor", country_hazards.output_factor(HAZARDS, 97) == 0.6)
check("the worst of the hazards running together stands", country_hazards.output_factor(HAZARDS, 100) == 0.6)
check("the window is closed at both ends", country_hazards.output_factor(HAZARDS, 95) == 0.6 and country_hazards.output_factor(HAZARDS, 105) == 0.6
	  and country_hazards.output_factor(HAZARDS, 106) == 1.0)
check("a hazard dated by one year counts for that year", country_hazards.output_factor([HAZARDS[2]], 100) == 0.8 and country_hazards.output_factor([HAZARDS[2]], 101) == 1.0)

staff, pay = {"labourer": 2.0}, {"labourer": 10.0}.get
whole = books_at_country_prices(100.0, 20.0, staff, 1.0, 1.0, 3.0, 1.0, pay, False, 0.0, 1.0)
cut = books_at_country_prices(100.0, 20.0, staff, 1.0, 1.0, 3.0, 1.0, pay, False, 0.0, 0.6)
check("a plant's takings fall by the output factor; its upkeep and wages do not",
	  abs(cut.takings - 0.6 * whole.takings) < 1e-9 and cut.upkeep == whole.upkeep and cut.wages == whole.wages, (whole, cut))
check("a ramped-up concern's takings fall by the output factor",
	  abs(gross_at_country_prices(100.0, 3.0, 1.0, False, 0.6) - 0.6 * gross_at_country_prices(100.0, 3.0, 1.0, False, 1.0)) < 1e-9)


class Answers:
	def pay_per_person_year(self, trade):
		return 10.0

	def price_per_unit(self, material):
		return None


class Shared(StateWorld):
	year = 97

	def country_economy(self, country):
		return Answers()

	def book_takings(self, node_id, opened_year):
		return 100.0

	def book_upkeep(self, node_id):
		return 20.0

	def concern_staff(self, node_id):
		return {"labourer": 2.0}

	def span_factor(self, size):
		return 1.0

	def market_factor_at(self, node_id, unit_price):
		return 1.0

	def in_goods_category(self, node_id):
		return False

	def book_takings_at_full_ramp(self, node_id):
		return 100.0


def country_world(hazards, shared):
	registry = ActorRegistry(ActorsState(home_country="home"))
	profile = CountryProfile(country="far", population=24000.0, extra={"hazards": hazards})
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0, params={})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home", extra={"hazards": [{"years": [0, 999], "output_factor": 0.01}]}),
										  "far": profile})
	return CountryWorld(shared, registry.state.countries["far"], registry)


war = country_world(HAZARDS, Shared())
peace = country_world([], Shared())
check("a country's output factor is its own hazards' at the year", war.output_factor() == 0.6 and peace.output_factor() == 1.0)
check("its plant books take the factor off the takings",
	  abs(war.plant_books("shop", 90, 0.0, 1.0).takings - 0.6 * peace.plant_books("shop", 90, 0.0, 1.0).takings) < 1e-9)
check("its ramped-up takings take it too", abs(war.concern_gross("shop") - 0.6 * peace.concern_gross("shop")) < 1e-9)
