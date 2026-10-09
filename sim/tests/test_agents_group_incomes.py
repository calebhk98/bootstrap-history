"""Complaint 110: groups from measured sources beyond displaced producers and employers. A stratum's
fall in earnings or in property income, and the fall in the profit of firms, each form a group whose size
and grievance are the simulated quantities. Small fixtures, no whole game."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CountryProfile, Sector
from sim.agents.group_tuning import STRATUM_GRIEVANCE_THRESHOLD
from sim.agents.strata_seed import strata_spawner
from sim.agents.tuning_strata import STRATUM_WORKING_SHARE

from .agents_fake_world import FakeWorld


class IncomeWorld(FakeWorld):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.pay = {"labourer": 150.0, "artisan": 400.0}

	def subsistence_cost_per_person_year(self):
		return 100.0

	def need_floor_costs_per_person_year(self):
		return {"food": 100.0, "shelter": 40.0}

	def pay_per_person_year(self, trade):
		return self.pay[trade]

	def observed_stratum(self, country, name):
		return None


DEFINITIONS = [{"name": "toilers", "share": 0.6, "trade": "labourer"},
			   {"name": "weavers", "share": 0.2, "trade": "artisan"},
			   {"name": "owners", "share": 0.01, "property_share": 0.3}]


def build():
	state = ActorsState(home_country="home")
	state.countries["home"] = CountryProfile(country="home", population=100000.0, strata=DEFINITIONS)
	registry = ActorRegistry(state)
	world = IncomeWorld()
	strata_spawner(registry, world)
	return registry, world


def stratum(registry, name):
	return registry.actors["stratum:home:" + name]


def settle_welfare(registry, world):
	"""Each stratum's welfare as its year would set it: its income over its food bill."""
	from sim.agents.stratum_year import own_income
	for actor in registry.of_kind("stratum"):
		food_bill = actor.record.members * 100.0
		actor.record.welfare = own_income(actor, world) / food_bill if food_bill > 0.0 else 0.0


registry, world = build()
strata = registry.of_kind("stratum")
settle_welfare(registry, world)
Sector.remember_welfare(strata, world)
check("steady earnings and rents organise nobody", Sector.of_strata(strata, world) == [])

# ---- workers: the pay of their trade falls -------------------------------------------------------
toilers = stratum(registry, "toilers").record
world.pay["labourer"] = 100.0
settle_welfare(registry, world)
found = {(sector.kind, sector.subject): sector for sector in Sector.of_strata(strata, world)}
check("a trade whose pay falls below what its workers expected forms a group of workers",
	  ("displaced_workers", "toilers") in found, list(found))
workers = found[("displaced_workers", "toilers")]
working = toilers.members * STRATUM_WORKING_SHARE
check("the group is the working people of the stratum", abs(workers.members - working) < 1e-6 * working, workers.members)
check("their loss is the fall in pay times the people paid",
	  abs(workers.lost_income - working * 50.0) < 1e-6 * working * 50.0, workers.lost_income)
check("the grievance names the trade and the fall", "labourer" in workers.cause and "33%" in workers.cause, workers.cause)
check("other trades' workers whose pay held are not organised", ("displaced_workers", "weavers") not in found)
check("a fall the pay explains is not counted a second time as a general fall of the stratum's incomes",
	  ("falling_incomes", "toilers") not in found, list(found))

# ---- landholders: property income falls ----------------------------------------------------------
registry, world = build()
strata = registry.of_kind("stratum")
settle_welfare(registry, world)
Sector.remember_welfare(strata, world)
before = world.output
world.output = before * 0.5
settle_welfare(registry, world)
found = {(sector.kind, sector.subject): sector for sector in Sector.of_strata(strata, world)}
check("a propertied stratum whose property income falls forms a group of landholders",
	  ("landholders", "owners") in found, list(found))
landholders = found[("landholders", "owners")]
lost = before * 0.3 * 0.5
check("the loss is the fall in the property income", abs(landholders.lost_income - lost) < 1e-6 * lost, landholders.lost_income)
check("the landholders are the stratum's own people",
	  abs(landholders.members - stratum(registry, "owners").record.members) < 1e-9)
check("the grievance says rents fell", "rents" in landholders.cause, landholders.cause)

# ---- what the pay of a trade and rents do not explain stays a general fall ------------------------
stratum(registry, "toilers").record.welfare *= 0.5
found = {(sector.kind, sector.subject): sector for sector in Sector.of_strata(strata, world)}
check("a fall in welfare beyond the measured pay and rents is left as a general fall of incomes",
	  ("falling_incomes", "toilers") in found, list(found))

# ---- a grievance fades as the fall becomes the new normal ------------------------------------------
for _year in range(80):
	Sector.remember_welfare(strata, world)
	settle_welfare(registry, world)
check("a fall that lasts is forgotten and the groups disband",
	  all(sector.lost_income < STRATUM_GRIEVANCE_THRESHOLD * sector.income_base for sector in Sector.of_strata(strata, world)))

# ---- owners of firms: profit falls below what they expected ---------------------------------------
def firm(name, margin):
	return SimpleNamespace(actor_id="firm:" + name, record=ActorRecord(kind="firm", last_margin=margin, name=name))


firms = [firm("a", 100.0), firm("b", 60.0), firm("c", 0.0)]
Sector.remember_margins(firms)
check("firms whose profit holds organise nobody", Sector.of_firms(firms, IncomeWorld()) == [])
firms[0].record.last_margin = 40.0
firms[1].record.last_margin = 20.0
firms[2].record.last_margin = 30.0
sectors = Sector.of_firms(firms, IncomeWorld())
check("firms whose profit falls form one group of owners", len(sectors) == 1 and sectors[0].kind == "firm_owners", sectors)
check("their loss is the profit that fell away, firm by firm",
	  abs(sectors[0].lost_income - 100.0) < 1e-9, sectors[0].lost_income)
check("a firm that earns more than it expected does not set off another's loss", sectors[0].members == 2, sectors[0].members)
check("the owners' income base is what they expected", abs(sectors[0].income_base - 160.0) < 1e-9, sectors[0].income_base)
check("the grievance names how many firms and by how much",
	  "2 firms" in sectors[0].cause and "62%" in sectors[0].cause, sectors[0].cause)
for _year in range(80):
	Sector.remember_margins(firms)
check("firm owners forget a fall that lasts", Sector.of_firms(firms, IncomeWorld()) == [])
gone = firm("d", 100.0)
Sector.remember_margins([gone])
gone.record.exited_year = 5
gone.record.last_margin = -50.0
check("a firm that has closed is not an owner with a grievance", Sector.of_firms([gone], IncomeWorld()) == [])
