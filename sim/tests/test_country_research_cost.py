"""Complaint 676: what pioneering a node costs is priced from the researching country's own quotes, pay and price level, and
every country's state originates research. The rules are called on written-out inputs and on stand-ins for the world."""

QUICK_TOPIC = True

from sim.agents import research, research_pricing
from sim.agents.api import ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, Government, seed_cast
from sim.agents.no_country_economy import NoCountryEconomy
from sim.agents.records import ActorRecord
from sim.agents.player_commands import CommandRejected

from .agents_fake_world import flat_world
from .country_state_world import StateWorld
from .harness import check

# ---- the plain functions
check("materials are summed at the quotes asked for each material's tonnes",
	  research_pricing.materials_at_quotes({"iron": 2.0, "wood": 3.0}, lambda material, tonnes: {"iron": 5.0, "wood": 1.0}[material] * tonnes) == 13.0)
check("a material quoted nowhere makes the materials' cost None, never zero",
	  research_pricing.materials_at_quotes({"iron": 2.0}, lambda material, tonnes: None) is None)
check("hours are summed at each trade's pay", research_pricing.hours_at_pay({"scholar": 10.0, "mason": 4.0}, {"scholar": 3.0, "mason": 2.0}.get) == 38.0)
check("the cost is capital at the price level plus materials plus labour",
	  research_pricing.cost_at_country_prices(100.0, 1.5, 13.0, 38.0) == 201.0)
check("the cost is None when the materials cannot be priced", research_pricing.cost_at_country_prices(100.0, 1.5, None, 38.0) is None)

# ---- a country's research part and a state beginning a project
NODE = {"id": "idea", "pre": [], "lab": {"scholar": 10.0}, "mat": {"iron": 1.0}, "cap": 100.0, "yrs": 2.0, "sch": 1, "art": 0, "risk": 0.0}


class Shared(StateWorld):
	"""The home world's answers; the countries differ only in pay, quotes and price level."""
	hours_per_person_year = 2000.0
	pay = {"home": 3.0, "rich": 6.0}
	iron_price = {"home": 2.0, "rich": 4.0}
	quoted = True

	def __init__(self):
		super().__init__()
		self.nodes["idea"] = NODE

	def material_tonnes(self, node_id):
		return {"iron": 0.5}

	def country_economy(self, country):
		world = self

		class Answers:
			def pay_per_person_year(self, trade):
				return world.pay[country] * world.hours_per_person_year

			def price_per_tonne(self, material):
				return world.iron_price[country] if world.quoted else None

			def people_of_trade(self, trade):
				return 5.0
		return Answers()

	def research_trades(self, family):
		return ["scholar"]

	def unsold_materials(self, actor, node_id):
		return []

	def purchasable_substitute_discount(self):
		return 0.9


def build(shared, country, money=1000.0):
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:" + country, country=country, kind="government", money=money, params={})
	profiles = {"home": CountryProfile(country="home"), country: CountryProfile(country=country, price_index=2.0 if country == "rich" else 1.0)}
	seed_cast(registry, "home", [entry], profiles)
	registry.staff.staff_fte_in_country = lambda trade, country_name, actor_id: 0.0
	return CountryWorld(shared, registry.state.countries[country], registry), registry.actors["government:" + country]


shared = Shared()
poor_world, _ = build(shared, "home")
rich_world, rich_state = build(shared, "rich")
home_cost = poor_world.research.research_cost("idea", 5)
rich_cost = rich_world.research.research_cost("idea", 5)
check("a country's cost is its capital at its price level, its materials at its quotes and its hours at its pay",
	  home_cost == 100.0 * 1.0 + 0.5 * 2.0 + 10.0 * 3.0 and rich_cost == 100.0 * 2.0 + 0.5 * 4.0 + 10.0 * 6.0, (home_cost, rich_cost))
check("two countries with different pay and prices price the same node differently", rich_cost > home_cost)

plan = research.plan(rich_state, "idea", rich_world)
check("the plan's labour is priced at the country's pay, not the home market's", plan["labour_cost"] == 10.0 * 6.0, plan["labour_cost"])
check("the plan's other money is the cost less that labour (plus the hiring premium for a trade not on staff)",
	  plan["money"] >= rich_cost - plan["labour_cost"] - 1e-9, plan)

shared.quoted = False
try:
	rich_world.research.research_cost("idea", 5)
	raised = None
except NoCountryEconomy as error:
	raised = error.figure
check("a material the country quotes nowhere refuses the cost, naming the figure", raised is not None and "idea" in raised, raised)
unpriced_refusal = None
try:
	research.begin(rich_state, "idea", rich_world)
except CommandRejected as error:
	unpriced_refusal = error.args[0].cause
check("beginning the work refuses with the cause no_country_prices", unpriced_refusal == "no_country_prices", unpriced_refusal)
shared.quoted = True

# ---- every country's state originates research
check("a country's state researches", rich_state.researches)
check("the home state researches", Government("government:home", ActorRecord(kind="government")).researches)
check("a foreign state with funds and scholars begins the project at its own cost",
	  research.begin(rich_state, "idea", rich_world).startswith("research begun") and rich_state.works["idea"]["research"]
	  and rich_state.works["idea"]["labour_cost"] == 60.0, rich_state.works)
