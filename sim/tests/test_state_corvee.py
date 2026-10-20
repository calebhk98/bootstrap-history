"""Complaint 621: a state's revenue forms may declare labour owed (days a year per working-age person or per household)
instead of money. The days are taken as hours from the people they fall on, and staff the state's works or its army
unpaid; conscripts count against the head count the country can spare; a form may be commuted to cash in part."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents import budget, budget_works, headcount, revenue, revenue_labour, state_works
from sim.agents.api import ActorRecord, Government, Hands
from sim.agents.tuning_spending import MASONRY_PERSON_YEARS_PER_M2
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

from .agents_fake_world import FakeWorld

WORKING_AGE = 1000.0
PEOPLE = 5000.0
WAGE = 10.0
HOURS_PER_YEAR = 2000.0
DAYS = 30.0
WORKS_DUE = {"form": "corvee", "basis": "labour_days", "rate": DAYS, "per": "working_age_person", "to": "works"}
ARMY_DUE = {"form": "conscription", "basis": "labour_days", "rate": 100.0, "per": "working_age_person", "to": "army"}


class CorveeWorld(FakeWorld):
	hours_per_person_year = HOURS_PER_YEAR

	def __init__(self, forms, hands=None, threat=0.0, army=0.0, urban=0.0, spectacle=0.0):
		super().__init__()
		self.urban, self.spectacle = urban, spectacle
		self.forms, self.hands, self.threat, self.army = forms, hands, threat, army
		self.state = Government("government:home", ActorRecord(kind="government", money=0.0))
		self.prices = {"wheat_kg": 2.0, "iron_bar_kg": 3.0}

	def government(self):
		return self.state

	def revenue_forms(self):
		return self.forms

	def revenue_assessments(self):
		return revenue.assess(self)

	def held_tiles(self):
		return ["a"]

	def national_people(self, trade):
		return WORKING_AGE

	def population_total(self):
		return PEOPLE

	def pay_per_person_year(self, trade):
		return WAGE

	def threat_pressure(self):
		return self.threat

	def territory(self):
		return SimpleNamespace(frontier_km=600.0, coast_km=0.0, road_km=0.0)

	def urban_population(self):
		return self.urban

	def state_weights(self):
		return {"spectacle": self.spectacle}

	def subsistence_kg_per_person_year(self):
		return 200.0

	def commodity_of(self, material):
		return material

	def country_strata(self):
		return []

	def local_staff(self, trade, people):
		return people

	def army_wanted(self):
		return self.army

	def equipment_kg_per_soldier(self):
		return 1.0

	def trade_exists(self, trade):
		return False

	def state_capacity(self):
		return 0.5

	def state_hands(self):
		return self.hands

	def need_floor_costs_per_person_year(self):
		return {}

	def state_may_borrow(self, state):
		return False

	def state_revenue(self):
		return 1000.0

	def group_claims(self):
		return {}

	def patron_ask(self):
		return 0.0

	def soldiers_under_arms(self):
		return self.state.record.army


# ---- the form: days owed become person-days, hours, and a money's worth ---------------------------------------
world = CorveeWorld([WORKS_DUE])
assessed = revenue.assess(world)[0]
check("a corvee of N days a working-age person owes N days from each",
	  abs(assessed.person_days - DAYS * WORKING_AGE) < 1e-9 and assessed.labour_to == "works" and assessed.in_labour, assessed)
hours = assessed.person_days * revenue_labour.HOURS_PER_WORKING_DAY
check("the days are hours of the people's working time", abs(assessed.hours - hours) < 1e-9, (assessed.hours, hours))
check("the labour is worth the wage of the person-years it comes to",
	  abs(assessed.money - hours / HOURS_PER_YEAR * WAGE) < 1e-9, assessed)
check("labour owed brings no coin to the purse", assessed.coin_money == 0.0, assessed)
per_household = revenue.assess(CorveeWorld([dict(WORKS_DUE, per="household")]))[0]
check("a corvee per household falls on the households, not the persons",
	  abs(per_household.person_days - DAYS * PEOPLE / PERSONS_PER_HOUSEHOLD) < 1e-9, per_household)

# ---- receiving it: hours owed are booked, no coin is made ---------------------------------------------------------
world = CorveeWorld([WORKS_DUE])
world.state.receive_revenue(world)
check("receiving a corvee books the hours owed to the works, and credits no money",
	  abs(world.state.record.corvee_due["works"] - hours) < 1e-9 and world.state.money == 0.0,
	  (world.state.record.corvee_due, world.state.money))
commuted = CorveeWorld([dict(WORKS_DUE, commute=0.4)])
commuted.state.receive_revenue(commuted)
check("a commuted share is cash, the rest stays labour",
	  abs(commuted.state.record.corvee_due["works"] - 0.6 * hours) < 1e-9
	  and abs(commuted.state.money - 0.4 * assessed.money) < 1e-9, (commuted.state.record.corvee_due, commuted.state.money))

# ---- the labour staffs the works unpaid ----------------------------------------------------------------------------
world = CorveeWorld([WORKS_DUE], threat=0.05, urban=1000.0)
state_works.held(world)
upkeep_before = {line.name: line for line in budget_works.works_upkeep_lines(world)}
years = hours / HOURS_PER_YEAR
reduced, spare = revenue_labour.offset_upkeep(list(upkeep_before.values()), years)
saved = sum(line.labour.get("mason", 0.0) for line in upkeep_before.values()) - sum(line.labour.get("mason", 0.0) for line in reduced)
check("corvee labour takes the place of the masons the upkeep would hire, person-year for person-year",
	  abs(saved - min(years, sum(line.labour.get("mason", 0.0) for line in upkeep_before.values()))) < 1e-9, (saved, years))
check("the upkeep it covers costs the state no wages",
	  sum(line.money for line in reduced) < sum(line.money for line in upkeep_before.values()), reduced)
world = CorveeWorld([WORKS_DUE], threat=0.05, urban=1000.0, spectacle=1.0)
state_works.held(world)
stock_before = state_works.held(world)["capital_buildings"]
world.state.record.corvee_spare_years = 3.0
world.state.build_works_by_corvee(world)
raised = state_works.held(world)["capital_buildings"] - stock_before
check("spare corvee labour raises the works the state lacks, at the masonry a person-year builds",
	  abs(raised - 3.0 / MASONRY_PERSON_YEARS_PER_M2) < 1e-9, raised)
check("it pays nobody for it", world.state.money == 0.0 and not world.state.record.outlays, world.state.record.outlays)

# ---- conscripts count against the pool the country can spare ------------------------------------------------
hands = Hands(working_age=WORKING_AGE, farm_hands=600.0, food_ratio=1.0)
world = CorveeWorld([ARMY_DUE], hands=hands, army=0.0)
due_years = ARMY_DUE["rate"] * WORKING_AGE * revenue_labour.HOURS_PER_WORKING_DAY / HOURS_PER_YEAR
check("the conscription asked is more than the country can spare", due_years > 400.0, due_years)
world.state.pay_standing_need(world)
booked = world.state.record.headcount["army"]
check("conscripts are drawn from the same pool as every other head count: the shortfall is booked with its cause",
	  booked["wanted"] >= due_years - 1e-6 and booked["granted"] <= 400.0 + 1e-6 and booked["cause"] == headcount.FARM_HANDS, booked)
check("the hours taken are those of the conscripts the country could spare",
	  abs(world.state.record.corvee_hours["army"] - booked["granted"] * HOURS_PER_YEAR) < 1e-6,
	  (world.state.record.corvee_hours, booked))
check("conscripts are not paid", sum(line.wages for line in budget.army_line(world, 400.0, 400.0)) == 0.0)
paid = budget.army_line(world, 400.0, 100.0)[0]
check("only the soldiers who are not conscripts draw pay", abs(paid.wages - 300.0 * WAGE) < 1e-9 and paid.labour == {"soldier": 300.0}, paid)

world = CorveeWorld([ARMY_DUE], hands=hands, army=100.0)
world.state.pay_standing_need(world)
check("a standing army larger than the conscripts is made up of them and paid soldiers",
	  world.state.record.army >= 100.0 - 1e-6, world.state.record.army)
