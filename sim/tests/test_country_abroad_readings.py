"""Complaint 649: the site rent, the manager's hours, the takings of a ramped-up concern and the yearly costs an entrant weighs are
read from the country the actor stands in. The rules are called on built inputs; a figure the country keeps no record of
makes the reading None and the actor does not enter, never the home figure. The home world's figures are unchanged."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import business_books, firm_entry, state_enterprises
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, Government, seed_cast
from sim.agents.country_state_site import costs_at_country_prices, gross_at_country_prices, rent_of_site
from sim.agents.tuning import MANAGEMENT_SPAN_OF_CONTROL

from .agents_fake_world import make_node
from .country_state_world import StateWorld

STAFF = {"mason": 2.0, "labourer": 3.0}
PAY = {"mason": 14.0, "labourer": 10.0}
BOOK_TAKINGS, BOOK_UPKEEP = 100.0, 20.0
COST_SCALE = 3.0
SPAN = 1.0
HECTARES = 2.5
COUNTRY_RENT = 8.0
HOME_RENT = 99.0
HOME_WAGE_PER_HOUR = 7.0


def pay(trade):
	return PAY.get(trade)


# ---- the rules, on built inputs ---------------------------------------------------------------
check("a site costs its hectares at the country's rent per hectare", rent_of_site(HECTARES, COUNTRY_RENT) == HECTARES * COUNTRY_RENT)
check("a country that let no land has no rent for a site (None)", rent_of_site(HECTARES, None) is None)
check("a ramped-up concern takes the book figure at the country's cost scale and market factor",
	  gross_at_country_prices(BOOK_TAKINGS, COST_SCALE, 1.25, False, 1.0) == BOOK_TAKINGS * COST_SCALE * 1.25)
check("a concern in a goods category has no takings in a country (None)", gross_at_country_prices(BOOK_TAKINGS, COST_SCALE, 1.0, True, 1.0) is None)
check("a plant's yearly costs are the book upkeep at the cost scale and the crew's pay in the country",
	  costs_at_country_prices(BOOK_UPKEEP, STAFF, COST_SCALE, SPAN, pay) == (BOOK_UPKEEP * COST_SCALE, 2.0 * 14.0 + 3.0 * 10.0))
check("a crew with a trade the country pays nothing for has no costs (None)",
	  costs_at_country_prices(BOOK_UPKEEP, {"astronomer": 1.0}, COST_SCALE, SPAN, pay) is None)


# ---- a world with its own (home) figures that a country's reading must not use ----------------
class Answers:
	"""The country's economy: its pay, its unit prices and its land rent (None where no land was let)."""
	rent = COUNTRY_RENT

	def pay_per_person_year(self, trade):
		return pay(trade)

	def price_per_unit(self, material):
		return None

	def land_rent_at(self, tile):
		return self.rent


class NoLandAnswers(Answers):
	rent = None


class HomeShared(StateWorld):
	answers = Answers()
	goods_category = False

	def __init__(self):
		super().__init__()
		self.nodes["shop"] = make_node("shop", hours=4000.0, revenue=500.0, upkeep=40.0)

	def book_takings_at_full_ramp(self, node_id):
		return BOOK_TAKINGS

	def book_upkeep(self, node_id):
		return BOOK_UPKEEP

	def concern_staff(self, node_id):
		return STAFF

	def span_factor(self, capacity):
		return SPAN

	def market_factor_at(self, node_id, unit_price):
		return 1.0

	def in_goods_category(self, node_id):
		return self.goods_category

	def site_hectares(self, node_id, capacity=1.0):
		return HECTARES * capacity

	def site_rent(self, node_id, capacity=1.0, tile=None):
		return HOME_RENT

	def country_economy(self, country):
		return self.answers


class NoPart(HomeShared):
	def country_economy(self, country):
		return None


class NoLandLet(HomeShared):
	answers = NoLandAnswers()


class GoodsCategory(HomeShared):
	goods_category = True


def country_world(shared):
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0e6, params={})
	profile = CountryProfile(country="far", population=24000.0)
	profile.price_index = COST_SCALE
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": profile})
	return CountryWorld(shared, registry.state.countries["far"], registry)


world = country_world(HomeShared())
rent = world.site_rent("shop", 2.0, "far_tile")
check("a country's site rent is its hectares at the country's rent, not the home world's", rent == HECTARES * 2.0 * COUNTRY_RENT, rent)
check("a country the economy has no part for has no site rent (None)", country_world(NoPart()).site_rent("shop", 1.0, None) is None)
check("a country that let no land has no site rent (None)", country_world(NoLandLet()).site_rent("shop", 1.0, None) is None)

check("a country's ramped-up concern takes the book figure at its cost scale",
	  world.concern_gross("shop") == BOOK_TAKINGS * COST_SCALE, world.concern_gross("shop"))
check("...none where the economy has no part for the country (None)", country_world(NoPart()).concern_gross("shop") is None)
check("...none for a goods category (None)", country_world(GoodsCategory()).concern_gross("shop") is None)

costs = world.plant_costs("shop")
check("a country's yearly costs are its own, not the home world's", costs == (BOOK_UPKEEP * COST_SCALE, 2.0 * 14.0 + 3.0 * 10.0), costs)
check("...none where the economy has no part for the country (None)", country_world(NoPart()).plant_costs("shop") is None)
check("a country's hourly pay is its person-year over the hours of a year", world.hourly_pay("mason") == 14.0 / world.hours_per_person_year)
check("...none for a trade it pays nothing for (None)", world.hourly_pay("astronomer") is None)


# ---- the manager's hours are paid at the best paid trade of the country ---------------------------
manager = firm_entry.management_cost(world, "shop", 2.0)
check("a country's manager hours cost the best paid trade's pay over the span of control, not the home quote",
	  abs(manager - 5.0 * 2.0 / MANAGEMENT_SPAN_OF_CONTROL * 14.0) < 1e-9, manager)
check("a country the economy has no part for has no manager cost (None)", firm_entry.management_cost(country_world(NoPart()), "shop", 1.0) is None)
check("carrying a concern needs both the rent and the manager: missing either is None",
	  firm_entry.carrying_cost(country_world(NoLandLet()), "shop") is None and firm_entry.carrying_cost(country_world(NoPart()), "shop") is None
	  and firm_entry.carrying_cost(world, "shop", 1.0) == HECTARES * COUNTRY_RENT + firm_entry.management_cost(world, "shop", 1.0))
check("the yearly costs an entrant weighs are the world's plant costs",
	  business_books.yearly_costs(world, "shop") == costs and business_books.yearly_costs(country_world(NoPart()), "shop") is None)


# ---- the entry decision: a state abroad opens only the entry whose figures it can read -----------
class MonopolyShared(HomeShared):
	def __init__(self):
		super().__init__()
		self.nodes["shop"]["makes"] = ["bricks_kg"]

	def concerns_making(self, material):
		return {"shop"}

	def concern_gross(self, node_id):
		return 1.0e9      # the home world's takings: a country's state must not use them


class NoPartMonopoly(MonopolyShared):
	def country_economy(self, country):
		return None


def monopoly_state():
	state = Government("government:far", ActorRecord(kind="government", country="far", money=1.0e6))
	state.record.state_monopolies = {"bricks_kg"}
	state.knows = lambda entry_key, scope: True
	return state


check("a state abroad opens the entry that earns by its own country's figures",
	  state_enterprises.entries_for(monopoly_state(), country_world(MonopolyShared())) == ["shop"])
check("a state abroad whose country has no takings for the entry (None) does not open it, whatever the home world takes",
	  state_enterprises.entries_for(monopoly_state(), country_world(NoPartMonopoly())) == [])


# ---- the home world gives the figures it always did ---------------------------------------------
class Home(StateWorld):
	def __init__(self):
		super().__init__()
		self.nodes["shop"] = make_node("shop", hours=4000.0, revenue=500.0, upkeep=40.0)
		self.labour_market.wage_per_hour = HOME_WAGE_PER_HOUR


home = Home()
people = sum(home.concern_staff("shop").values()) * 2.0
check("the home manager cost is the hours of the staff over the span at the best quote, as before",
	  firm_entry.management_cost(home, "shop", 2.0) == people / MANAGEMENT_SPAN_OF_CONTROL * home.hours_per_person_year * HOME_WAGE_PER_HOUR)
check("the home yearly costs are its upkeep and its wage bill, as before",
	  business_books.yearly_costs(home, "shop") == (home.upkeep("shop"), home.concern_wage_bill("shop")))
check("the home carrying cost is its site rent and manager cost, as before",
	  firm_entry.carrying_cost(home, "shop", 2.0) == home.site_rent("shop", 2.0, None) + firm_entry.management_cost(home, "shop", 2.0))
