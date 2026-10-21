"""Complaint 593: a country's state is the one `Government`, scoped to the country. Its revenue is assessed from the
forms its civilisation file declares, on the country's own people and land; its budget keeps the same lines as the
home state's for the same inputs. The rules are called directly, with no whole game."""

QUICK_TOPIC = True

from .harness import check

from sim import simulator as S
from sim.agents import budget, revenue
from sim.agents import api as agents_api
from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, Government, seed_cast
from sim.agents.cast import profile_from_civilisation
from sim.geography.api import territory

from .country_state_world import StateWorld

TRADES = {"labourer": 10.0, "soldier": 12.0, "scribe": 15.0, "mason": 14.0}
WORKING_AGE = 6000.0
COUNTRY_PRICE = 5.0     # the country's own price of any material; the home world quotes 2 (StateWorld)
COUNTRY_COIN_STOCK = 700.0
SKILLED_PEOPLE = 0.25 * WORKING_AGE    # the people the country's labour markets hold in any skilled trade
COUNTRY_TRADE = {"in": 4000.0, "out": 1500.0}     # what crossed the country's border last year, in its money


class CountryAnswers:
	def pay_per_person_year(self, trade):
		return TRADES.get(trade, 11.0)

	def society_output(self):
		return 1.0e6

	def need_floor_costs_per_person_year(self):
		return {"food": 5.0}

	def price_per_tonne(self, material):
		return COUNTRY_PRICE if material != "unpriced_kg" else None

	def coin_regime(self):
		return "struck_coin"

	def coin_stock_value(self):
		return COUNTRY_COIN_STOCK

	def trade_value(self, direction):
		return COUNTRY_TRADE[direction]

	def people_of_trade(self, trade):
		return SKILLED_PEOPLE


class Shared(StateWorld):
	def country_economy(self, country):
		return CountryAnswers()

	def notice_over(self, scale, capacity=None):
		return 0.0


class HomeInputs(Shared):
	"""The home world answering the questions a country's world answers from its profile, with the same figures."""

	def __init__(self, profile, assessed):
		super().__init__()
		self.profile, self.assessed = profile, assessed
		record = type("Record", (), {"accession_due": False, "works_stock": {}, "army": 0.0, "levers": {}})()
		self.government_actor = type("Government", (), {"record": record})()

	def population_total(self):
		return self.profile.population

	def state_reach(self):
		return 0.5

	def urban_population(self):
		return self.profile.population * self.profile.urban_fraction

	def territory(self):
		return territory.holdings(self.profile.home_tiles)

	def national_people(self, trade):
		return WORKING_AGE if trade == "labourer" else SKILLED_PEOPLE

	def threat_pressure(self):
		return 0.0

	def army_wanted(self):
		return float(self.profile.extra["standing_army"])

	def revenue_assessments(self):
		return self.assessed

	def pay_per_person_year(self, trade):
		return TRADES.get(trade, 11.0)

	def material_cost(self, material, tonnes):
		return COUNTRY_PRICE * tonnes

	def material_price(self, material):
		return COUNTRY_PRICE


FORMS = [{"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.1},
		 {"form": "land_tax", "basis": "harvest", "rate": 0.2, "paid_in": "wheat_kg"},
		 {"form": "import_duty", "basis": "imports_value", "rate": 0.05}]


def profile_with(forms, army=100.0):
	profile = CountryProfile(country="far", population=24000.0, urban_fraction=0.1, tax_share=0.1,
							 home_tiles=[], extra={"standing_army": army, "state_revenue": forms})
	profile.cohorts = {"children": 10000.0, "working_age": WORKING_AGE, "elderly": 8000.0}
	profile.farm = {"hectares": 500.0, "quality": 1.0, "stock_kg": 0.0, "harvest_kg": 900000.0, "shortfall_kg": 0.0, "years": 3.0}
	return profile


def country_world(profile, shared=None):
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0e6,
					  params={"revenue_forms": list(profile.extra.get("state_revenue") or ())})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home"), "far": profile})
	return CountryWorld(shared or Shared(), registry.state.countries["far"], registry), registry


# ---- there is one kind of state --------------------------------------------------------------
check("no foreign-government class remains", not hasattr(agents_api, "Foreign" + "Government"))
world, registry = country_world(profile_with(FORMS))
check("a country buys at its own prices, not the home market's",
	  world.material_cost("iron_kg", 3.0) == 3.0 * COUNTRY_PRICE and world.material_price("iron_kg") == COUNTRY_PRICE,
	  (world.material_cost("iron_kg", 3.0), world.material_price("iron_kg")))
check("a material its markets do not quote is not on sale (None), not free and not the home price", world.material_cost("unpriced_kg", 3.0) is None)
check("its coin standard and coin stock are its own, not the home's",
	  world.coin_regime() == "struck_coin" and world.coin_stock_value() == COUNTRY_COIN_STOCK)
check("a country's state is the one Government, scoped to the country",
	  type(registry.actors["government:far"]) is Government and registry.actors["government:far"].record.country == "far")

# ---- revenue is assessed from the declared forms ---------------------------------------------
check("a country's forms are the ones its civilisation file declares",
	  profile_from_civilisation({"id": "far", "state_revenue": FORMS}).extra["state_revenue"] == FORMS)
han = S.load_civ("han_china_100ad")
check("the forms of a shipped civilisation reach its profile whole",
	  profile_from_civilisation(han).extra["state_revenue"] == han["state_revenue"] and len(han["state_revenue"]) > 1)
check("a country's world offers the forms its profile carries", world.revenue_forms() == FORMS)
assessed = {assessment.form: assessment for assessment in revenue.assess(world)}
check("every declared form is assessed, in order", list(assessed) == [form["form"] for form in FORMS], list(assessed))
soldiers = world.soldiers_under_arms()
poll = assessed["poll_tax"]
check("a poll tax is its rate on the working age less the soldiers, at the country's own pay",
	  abs(poll.base - (WORKING_AGE - soldiers) * 10.0) < 1e-6 and abs(poll.money - 0.1 * poll.base) < 1e-6, poll)
land = assessed["land_tax"]
check("a levy on the harvest is its rate on the country's own harvest, taken in kind",
	  abs(land.tonnes - 0.2 * 900.0) < 1e-9 and land.material == "wheat_kg" and abs(land.money - 0.2 * 900.0 * COUNTRY_PRICE) < 1e-9, land)
duty = assessed["import_duty"]
check("a customs form is its rate on the imports the country's own trade book shows",
	  abs(duty.base - COUNTRY_TRADE["in"]) < 1e-9 and abs(duty.money - 0.05 * COUNTRY_TRADE["in"]) < 1e-9, duty)
check("a skilled trade's people are those its own labour markets hold; unskilled labour is the working age",
	  world.national_people("scribe") == SKILLED_PEOPLE and world.national_people("labourer") == WORKING_AGE)
check("the country's trade book is its own, not the home world's", world.trade_value("out") == COUNTRY_TRADE["out"])
check("the state's revenue is what its forms yield", abs(world.state_revenue() - sum(a.money for a in assessed.values())) < 1e-9)
bare_world, _ = country_world(profile_with([]))
check("a country declaring no forms raises nothing", bare_world.state_revenue() == 0.0 and bare_world.revenue_assessments() == [])
taxing_less = profile_with([dict(FORMS[0], rate=0.05)])
check("a lower declared rate yields less", country_world(taxing_less)[0].state_revenue() < poll.money)

# ---- the same budget lines as the home state, given the same inputs -----------------------------
profile = profile_with(FORMS)
world, registry = country_world(profile)
home = HomeInputs(profile, world.revenue_assessments())
home_lines = budget.standing_lines(home, 100.0)
country_lines = budget.standing_lines(world, 100.0)
check("a country's state keeps the lines the home state keeps",
	  [line.name for line in country_lines] == [line.name for line in home_lines] and len(country_lines) >= 3,
	  ([line.name for line in country_lines], [line.name for line in home_lines]))
check("...at the same cost in money, people and goods",
	  all(abs(a.money - b.money) < 1e-9 and a.labour == b.labour and a.materials == b.materials
		  for a, b in zip(country_lines, home_lines)), [(a.name, a.money, b.money) for a, b in zip(country_lines, home_lines)])
names = {line.name for line in country_lines}
check("the army, officials, guards, inspectors, collection of its forms, public buildings and dole are among them",
	  {"army", "administration", "guards", "inspectors", "tax_collection", "public_buildings", "dole"} <= names, names)
check("a country's collectors follow the forms it declares",
	  "tax_collection" not in {line.name for line in budget.standing_lines(country_world(profile_with([]))[0], 100.0)})

# ---- what the country holds is read from its own tiles ---------------------------------------
tiled = profile_with(FORMS)
tiled.home_tiles = list(profile_from_civilisation(han).home_tiles)[:6]
tiled_world, _ = country_world(tiled)
check("its roads and coast are those of the tiles it holds",
	  tiled_world.territory() == territory.holdings(tiled.home_tiles) and tiled_world.held_tiles() == tiled.home_tiles)
check("a country holding tiles keeps a road line; one holding none does not",
	  any(line.name == "roads" for line in budget.standing_lines(tiled_world, 0.0))
	  and not any(line.name == "roads" for line in budget.standing_lines(world, 0.0)))

# ---- a year of its state: the lines are paid from its own purse, to its own people ---------------
government = registry.actors["government:far"]
lines, share = government.pay_standing_need(world)
check("the state pays the lines it keeps from its purse", share > 0.0 and {line.name for line in lines} >= {"army", "administration"}, share)
check("revenue by form is booked for the forms it declares",
	  set(government.record.revenue_by_form) >= {form["form"] for form in FORMS[:2]}, government.record.revenue_by_form)
check("what it takes in kind enters its stores", government.record.stores.get("wheat_kg", 0.0) > 0.0, government.record.stores)
check("its own staff are not the founder's labour pool", world.local_staff("scribe", 50.0) == 0.0)
check("nobody is its patron and no interest group holds a claim on it", world.patron_ask() == 0.0 and world.group_claims() == {})
