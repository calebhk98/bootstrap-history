"""Complaint 649: a plant's books (takings, upkeep, wages) read the prices, wages and cost scale of the country it stands in.
The rule is called on built inputs; a figure the country keeps no record of makes the reading None, never the home figure."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, seed_cast
from sim.agents.business_plant_books import PlantBooks, books_at_country_prices, home_books, wage_bill_at

from .country_state_world import StateWorld

STAFF = {"mason": 2.0, "labourer": 3.0}
PAY = {"mason": 14.0, "labourer": 10.0}
BOOK_TAKINGS, BOOK_UPKEEP = 100.0, 20.0
COUNTRY_COST_SCALE = 3.0
SPAN = 1.5      # the management-span lift the world gives the size asked for
HOME_BOOKS = PlantBooks(7.0, 8.0, 9.0)    # what the home economy would state; a country's reading must never be this
CREW_PAY = 2.0 * PAY["mason"] + 3.0 * PAY["labourer"]


def pay(trade):
	return PAY.get(trade)


# ---- the rule, on built inputs -------------------------------------------------------------------
wages = wage_bill_at(STAFF, 2.0, SPAN, pay)
check("wages are each trade's people times a person-year of its pay in the country, lifted by the span of the size",
	  wages == SPAN * CREW_PAY, wages)
check("a crew with a trade the country pays nothing for has no wage bill (None)", wage_bill_at({"astronomer": 1.0}, 1.0, 1.0, pay) is None)
books = books_at_country_prices(BOOK_TAKINGS, BOOK_UPKEEP, STAFF, 2.0, SPAN, COUNTRY_COST_SCALE, 1.25, pay, False, 0.0)
# a lone operator's takings are its size's share of the market it fills: the figure per founding size
check("takings and upkeep are the tree's book figures at the country's cost scale, the size and the country's market factor",
	  books == PlantBooks(BOOK_TAKINGS * COUNTRY_COST_SCALE * 1.25, BOOK_UPKEEP * COUNTRY_COST_SCALE * 2.0, SPAN * CREW_PAY), books)
check("a concern with no market model splits its takings with its rivals",
	  books_at_country_prices(BOOK_TAKINGS, BOOK_UPKEEP, STAFF, 1.0, 1.0, 1.0, 1.0, pay, False, 1.0).takings == BOOK_TAKINGS / 2.0)
check("a goods category shares the home society's demand, which has no country record (None)",
	  books_at_country_prices(BOOK_TAKINGS, BOOK_UPKEEP, STAFF, 1.0, 1.0, 1.0, 1.0, pay, True, 0.0) is None)
check("a plant with a trade nobody pays for in the country has no books (None)",
	  books_at_country_prices(BOOK_TAKINGS, BOOK_UPKEEP, {"astronomer": 1.0}, 1.0, 1.0, 1.0, 1.0, pay, False, 0.0) is None)


# ---- the country's world reads them from its own economy, not the home world --------------------
class Answers:
	"""The country's economy: its pay and its unit prices (a good it quotes none of is None)."""
	def pay_per_person_year(self, trade):
		return pay(trade)

	def price_per_unit(self, material):
		return 6.0 if material == "bricks" else None


class HomeShared(StateWorld):
	"""A shared world whose own (home) figures differ from the country's; a country's reading must not use them."""
	in_category = False

	def book_takings(self, node_id, opened_year):
		return BOOK_TAKINGS

	def book_upkeep(self, node_id):
		return BOOK_UPKEEP

	def concern_staff(self, node_id):
		return STAFF

	def span_factor(self, capacity):
		return SPAN

	def market_factor_at(self, node_id, unit_price):
		"""The home long-run price of bricks is 4."""
		return 1.0 if unit_price("bricks") is None else unit_price("bricks") / 4.0

	def in_goods_category(self, node_id):
		return self.in_category

	def concern_takings(self, node_id, opened_year, rivals=0.0, capacity=1.0):
		return HOME_BOOKS.takings

	def upkeep(self, node_id, capacity=1.0):
		return HOME_BOOKS.upkeep

	def concern_wage_bill(self, node_id, capacity=1.0):
		return HOME_BOOKS.wages

	def country_economy(self, country):
		return Answers()


def country_world(profile, shared):
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0e6, params={})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": profile})
	return CountryWorld(shared, registry.state.countries["far"], registry)


profile = CountryProfile(country="far", population=24000.0)
profile.price_index = COUNTRY_COST_SCALE
read = country_world(profile, HomeShared()).plant_books("kiln", 90, 0.0, 2.0)
check("a country's plant is booked at the country's pay, prices and cost scale",
	  read == PlantBooks(BOOK_TAKINGS * COUNTRY_COST_SCALE * 1.5, BOOK_UPKEEP * COUNTRY_COST_SCALE * 2.0, SPAN * CREW_PAY), read)
check("...and none of it is the home economy's figure", read is not None and all(figure != home for figure, home in zip(read, HOME_BOOKS)))
check("the home economy's books are its own concern figures", home_books(HomeShared(), "kiln", 90, 0.0, 2.0) == HOME_BOOKS)

shared_in_category = HomeShared()
shared_in_category.in_category = True
check("a country's plant in a goods category has no books (None), not the home demand's",
	  country_world(profile, shared_in_category).plant_books("kiln", 90, 0.0, 2.0) is None)


class NoPart(HomeShared):
	def country_economy(self, country):
		return None


check("a country the economy has no part for has no books (None), not the home figures",
	  country_world(profile, NoPart()).plant_books("kiln", 90, 0.0, 2.0) is None)
