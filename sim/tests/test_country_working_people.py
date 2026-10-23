"""Complaint 649: the people unskilled labour can draw on in a country are the working people its own labour markets hold,
not its profile's working age; a country whose labour markets hold nobody (or that has no part in the economy) refuses with
a cause. The rule is called on the hand-built two-country economy and on a stand-in world."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, seed_cast
from sim.agents.no_country_economy import NoCountryEconomy
from sim.economy import country_figures
from sim.engine.economy_port_country import CountryAnswers
from sim.tests import economy_fixture as fixture

from .country_state_world import StateWorld

setup = fixture.two_country_setup()
economy, _outcomes = fixture.run(setup, years=4)

north = CountryAnswers(economy, fixture.NORTH, off_map_trade=lambda direction: 0.0)
home = CountryAnswers(economy, setup.civ_id, off_map_trade=lambda direction: 0.0)
north_by_trade = country_figures.people_by_trade(economy, fixture.NORTH)
check("a country's working people are the people its labour markets hold, over every trade",
	  abs(north.working_people() - sum(north_by_trade.values())) < 1e-6 and north.working_people() > north_by_trade["labourer"] - 1e-9,
	  (north.working_people(), north_by_trade))
check("...and not the other country's", abs(home.working_people() - north.working_people()) > 1.0, (home.working_people(), north.working_people()))
check("a country whose tiles hold no labour markets has none to count (None)", CountryAnswers(economy, "nowhere", off_map_trade=lambda direction: 0.0).working_people() is None)


MARKET_PEOPLE = 5400.0
PROFILE_WORKING_AGE = 12345.0


class Answers:
	def __init__(self, people):
		self.people = people

	def working_people(self):
		return self.people

	def people_of_trade(self, trade):
		return 7.0


class Shared(StateWorld):
	answers = Answers(MARKET_PEOPLE)

	def country_economy(self, country):
		return self.answers


def country_world(shared):
	registry = ActorRegistry(ActorsState(home_country="home"))
	profile = CountryProfile(country="far", population=24000.0)
	profile.cohorts = {"children": 1.0, "working_age": PROFILE_WORKING_AGE, "elderly": 1.0}
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0, params={})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": profile})
	return CountryWorld(shared, registry.state.countries["far"], registry)


def refuses(world, trade):
	try:
		world.national_people(trade)
	except NoCountryEconomy as error:
		return error.country
	return None


world = country_world(Shared())
check("unskilled labour is the working people the country's labour markets hold, not its profile's working age",
	  world.national_people("labourer") == MARKET_PEOPLE != PROFILE_WORKING_AGE, world.national_people("labourer"))
check("a skilled trade is the people its markets hold in the trade", world.national_people("scribe") == 7.0)


class Empty(Shared):
	answers = Answers(None)


class NoPart(Shared):
	def country_economy(self, country):
		return None


check("a country whose labour markets hold nobody refuses for unskilled labour, naming the country", refuses(country_world(Empty()), "labourer") == "far")
check("a country the economy has no part for refuses for every trade, never the working age",
	  refuses(country_world(NoPart()), "labourer") == "far" and refuses(country_world(NoPart()), "scribe") == "far")
