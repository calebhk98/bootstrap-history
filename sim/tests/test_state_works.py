"""Complaint 315: the lines the state's budget lacked are named, each with a stock or a driver from existing state:
walls from the frontier and the sack hazard, water works from the towns, a grain reserve in the stores, collectors
from what each revenue form raises, a campaign from the threat and the frontier, monuments from the state's taste
for spectacle, and a donative at a ruler's accession. A surplus buys the works the state lacks and nothing unnamed."""
from .harness import *  # noqa: F401,F403
from types import SimpleNamespace

from sim.agents import budget, budget_works, revenue, state_works
from sim.agents.api import Government
from sim.agents.records import ActorRecord
from sim.agents.tuning_spending import (ACCESSION_PROBABILITY_PER_YEAR, GRANARY_LOSS_SHARE_PER_YEAR,
										MASONRY_PERSON_YEARS_PER_M2, PUBLIC_BUILDING_LIFE_YEARS)
from sim.tests.agents_fake_world import FakeWorld

QUICK_TOPIC = True

GRAIN = "wheat_kg"


class WorksWorld(FakeWorld):
	def __init__(self, threat=0.0, spectacle=0.0, urban=1000.0, frontier_km=600.0):
		super().__init__()
		self.threat, self.spectacle, self.urban, self.frontier_km = threat, spectacle, urban, frontier_km
		self.state = Government("government:home", ActorRecord(kind="government", money=0.0))
		self.prices = {GRAIN: 2.0}
		self.assessments = []

	def government(self):
		return self.state

	def threat_pressure(self):
		return self.threat

	def territory(self):
		return SimpleNamespace(frontier_km=self.frontier_km, coast_km=0.0, road_km=0.0)

	def urban_population(self):
		return self.urban

	def state_weights(self):
		return {"spectacle": self.spectacle}

	def pay_per_person_year(self, trade):
		return 10.0

	def national_people(self, trade):
		return 1.0e6

	def subsistence_kg_per_person_year(self):
		return 200.0

	def commodity_of(self, material):
		return material

	def revenue_assessments(self):
		return self.assessments

	def country_strata(self):
		return []

	def need_floor_costs_per_person_year(self):
		return {}

	def local_staff(self, trade, people):
		return people


def lines_by_name(lines):
	return {line.name: line for line in lines}


# ---- walls follow the frontier and the hazard, not a table ------------------------------------------
calm, threatened = WorksWorld(threat=0.0), WorksWorld(threat=0.05)
check("a state with no sack hazard walls nothing", state_works.fortifications_wanted(calm) == 0.0)
check("walls follow the threat", state_works.fortifications_wanted(threatened) > 0.0)
longer = WorksWorld(threat=0.05, frontier_km=1200.0)
check("walls follow the length of the frontier",
      abs(state_works.fortifications_wanted(longer) - 2.0 * state_works.fortifications_wanted(threatened)) < 1e-6)
check("water works follow the towns", state_works.water_works_wanted(WorksWorld(urban=2000.0)) ==
      2.0 * state_works.water_works_wanted(WorksWorld(urban=1000.0)))
check("monuments follow the state's taste for spectacle: none without it",
      state_works.capital_buildings_wanted(calm) == 0.0 and state_works.capital_buildings_wanted(WorksWorld(spectacle=1.0)) > 0.0)

# ---- the stock stands at the opening for walls and water, not for monuments ---------------------------
world = WorksWorld(threat=0.05, spectacle=1.0)
stock = state_works.held(world)
check("walls and water works stand at the opening", stock["fortifications"] > 0.0 and stock["water_works"] > 0.0, stock)
check("monuments are raised from a surplus, so none stand at the opening", stock["capital_buildings"] == 0.0, stock)
upkeep = lines_by_name(budget_works.works_upkeep_lines(world))
check("upkeep is a named masons' line for each work held",
      set(upkeep) == {"fortifications", "water_works"} and "mason" in upkeep["fortifications"].labour, upkeep)
check("upkeep is the labour that replaces the stock once in a building's life",
      abs(upkeep["fortifications"].labour["mason"] - stock["fortifications"] * MASONRY_PERSON_YEARS_PER_M2 / PUBLIC_BUILDING_LIFE_YEARS) < 1e-6)
state_works.wear(stock, 0.5, 100.0)
check("works whose upkeep goes unpaid decay", stock["water_works"] < state_works.water_works_wanted(world), stock)

# ---- a surplus buys the works lacked, in people hired, and nothing else ------------------------------
world = WorksWorld(threat=0.05, spectacle=1.0)
state_works.held(world)
treasury = world.state
treasury.money = 1.0e9
before = treasury.money
treasury.build_works([], world)
check("a surplus raised the monuments the state lacked", state_works.held(world)["capital_buildings"] > 0.0, state_works.held(world))
paid = before - treasury.money
check("it paid masons for them", treasury.workforce.get("mason", 0.0) > 0.0 and paid > 0.0, treasury.workforce)
check("it built toward what it wants and no further",
      state_works.held(world)["capital_buildings"] <= state_works.capital_buildings_wanted(world) + 1e-6)
check("no outlay is an unnamed one", set(treasury.record.outlays) <= {"building capital_buildings"}, treasury.record.outlays)
sated = WorksWorld()
state_works.held(sated)
sated.state.money = 1.0e9
sated.state.build_works([], sated)
check("a state that wants nothing more keeps its surplus rather than spending it on unnamed works",
      sated.state.money == 1.0e9 and not sated.state.record.outlays, sated.state.record.outlays)

# ---- the granary: a reserve in the stores, spoilage, bought cheap, released dear ----------------------
world = WorksWorld()
treasury = world.state
target = treasury.granary_target(world)
check("the reserve is a target in years of the towns' food", target > 0.0, target)
treasury.record.stores[GRAIN] = target * 3.0
sold = treasury.keep_granary(world)
check("grain above the target is sold into the market", sold > 0.0 and world.sales[-1][1] == GRAIN, world.sales)
check("what is kept is the target less spoilage",
      abs(treasury.record.stores[GRAIN] - target * 3.0 * (1.0 - GRANARY_LOSS_SHARE_PER_YEAR) + sold) < 1e-6,
      treasury.record.stores)
world = WorksWorld()
treasury = world.state
treasury.record.stores[GRAIN] = target
world.prices[GRAIN] = 2.0
treasury.keep_granary(world)
world.prices[GRAIN] = 1.0
treasury.record.stores[GRAIN] = 0.1 * target
spent = treasury.restock_granary(1.0e9, world)
check("below the target it buys when the price is below normal", spent > 0.0 and world.purchases, (spent, world.purchases))
check("and holds what it bought", treasury.record.stores[GRAIN] > 0.1 * target, treasury.record.stores)
world.prices[GRAIN] = 5.0
spent = treasury.restock_granary(1.0e9, world)
check("it does not buy when grain is dear", spent == 0.0, spent)
before_sales = len(world.sales)
treasury.record.stores[GRAIN] = target
treasury.keep_granary(world)
check("it releases grain when the market is dear", len(world.sales) > before_sales, world.sales)

# ---- tax collection: collectors in proportion to what each form raises ----------------------------------
world = WorksWorld()
world.assessments = [revenue.Assessment("tithe", "harvest", 100000.0, 0.1, 10000.0),
                     revenue.Assessment("duty", "imports_value", 100000.0, 0.025, 2500.0)]
collection = lines_by_name(budget_works.collection_line(world))["tax_collection"]
check("collection is a named line of collectors", "scribe" in collection.labour, collection)
world.assessments = world.assessments[:1]
farm = budget_works.collection_line(world)[0].labour["scribe"]
world.assessments = [revenue.Assessment("duty", "imports_value", 100000.0, 0.025, 2500.0)]
customs = budget_works.collection_line(world)[0].labour["scribe"]
check("a form on the harvest takes more collectors per unit of base than a customs post", farm > customs, (farm, customs))
world.assessments = []
check("a state raising nothing keeps no collectors", budget_works.collection_line(world) == [])

# ---- a campaign: grain for the part of the army the threat sends out ------------------------------------
check("without a threat no force takes the field", budget_works.campaign_line(WorksWorld(), 1000.0) == [])
campaign = lines_by_name(budget_works.campaign_line(WorksWorld(threat=0.05), 1000.0))["campaign"]
check("the campaign is grain", GRAIN in campaign.materials and campaign.money > 0.0, campaign)
farther = lines_by_name(budget_works.campaign_line(WorksWorld(threat=0.05, frontier_km=1200.0), 1000.0))["campaign"]
check("a longer march costs more", farther.money > campaign.money)

# ---- a donative when a new ruler accedes -----------------------------------------------------------------
world = WorksWorld()
check("no donative is owed before an accession", budget_works.donative_line(world, 1000.0) == [])
world.state.record.accession_due = True
donative = lines_by_name(budget_works.donative_line(world, 1000.0))["donative"]
check("after an accession each soldier is owed a gift", donative.transfer == 1000.0 * 10.0, donative)
accessions = 0
for year in range(400):
	world.year = year
	world.state.record.accession_due = False
	world.state.accede(world)
	accessions += world.state.record.accession_due
check("accessions are a chance each year", 0.0 < accessions / 400.0 < 3.0 * ACCESSION_PROBABILITY_PER_YEAR, accessions)

# ---- all of them are standing lines of the budget --------------------------------------------------------
world = WorksWorld(threat=0.05)
world.state.record.accession_due = True
world.assessments = [revenue.Assessment("tithe", "harvest", 100000.0, 0.1, 10000.0)]
world.army_wanted = lambda: 1000.0
world.population_total = lambda: 1.0e5
world.state_capacity = lambda: 0.5
world.equipment_kg_per_soldier = lambda: 0.0
world.trade_exists = lambda trade: False
names = {line.name for line in budget.standing_lines(world)}
check("the budget names fortifications, water works, collection, a campaign and a donative",
      {"fortifications", "water_works", "tax_collection", "campaign", "donative"} <= names, sorted(names))
