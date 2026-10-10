"""Complaint 110: the stakes of landholders (the land market's rent), workers out of a job (hours left unhired, and the
technique that displaced them), a church, an academy, the state's office-holders and its army; and a prohibition that
reaches a technique through its substitutes. Small fixtures, no whole game."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents import group_servants
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CountryProfile, Government, Sector
from sim.agents.foundation import Academy, Church
from sim.agents.group import BANNING_KINDS, state_response
from sim.agents.group_jobs import JOBLESS_WORKERS, displacing_technique
from sim.agents.group_reach import subjects_reached
from sim.agents.strata_seed import strata_spawner
from sim.agents.tuning_strata import STRATUM_WORKING_SHARE

from .agents_fake_world import FakeWorld


class StakeWorld(FakeWorld):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pay = {"labourer": 150.0, "artisan": 400.0, "priest": 200.0, "scholar": 300.0, "scribe": 250.0, "soldier": 180.0}
        self.rent = {}
        self.idle = {}
        self.technique = None
        self.rent_per_hectare = 2.0
        self.tithable = 1000.0
        self.revenue = 10000.0
        self.strata = []
        self.said = []

    def subsistence_cost_per_person_year(self):
        return 100.0

    def need_floor_costs_per_person_year(self):
        return {"food": 100.0, "shelter": 40.0}

    def pay_per_person_year(self, trade):
        return self.pay[trade]

    def observed_stratum(self, country, name):
        return None

    def land_rent_paid_by_tile(self):
        return dict(self.rent)

    def idle_hours_by_trade(self):
        return dict(self.idle)

    def displacing_technique(self, trade):
        return self.technique

    def technique_name(self, node_id):
        return "the " + node_id

    def land_rent_per_hectare(self):
        return self.rent_per_hectare

    def tithable_sales_value(self, need_id):
        return self.tithable

    def country_strata(self):
        return self.strata

    def state_revenue(self):
        return self.revenue

    def state_capacity(self):
        return 0.5

    def money_text(self, amount, grouped=False, short=False):
        return "%d" % round(amount)

    def plain_number(self, value):
        return "%d" % round(value)

    def say(self, text):
        self.said.append(text)


DEFINITIONS = [{"name": "toilers", "share": 0.6, "trade": "labourer"},
               {"name": "owners", "share": 0.01, "property_share": 0.3},
               {"name": "lords", "share": 0.01, "property_share": 0.1}]


def build(definitions=DEFINITIONS):
    state = ActorsState(home_country="home")
    state.countries["home"] = CountryProfile(country="home", population=100000.0, strata=definitions)
    registry = ActorRegistry(state)
    world = StakeWorld()
    strata_spawner(registry, world)
    world.strata = registry.of_kind("stratum")
    return registry, world


def by_key(sectors):
    return {(sector.kind, sector.subject): sector for sector in sectors}


# ---- landholders: the rent of the land let ----------------------------------------------------------------------------
registry, world = build()
strata = registry.of_kind("stratum")
world.rent = {"plain": 600.0, "hills": 400.0}
Sector.remember_welfare(strata, world)
owners = registry.actors["stratum:home:owners"].record
lords = registry.actors["stratum:home:lords"].record
check("a stratum's property income is read from the land market's rent where land was let",
      abs(owners.income_reference["property"] - 750.0) < 1e-9 and abs(lords.income_reference["property"] - 250.0) < 1e-9,
      (owners.income_reference, lords.income_reference))
check("steady rents organise no landholders", "landholders" not in {sector.kind for sector in Sector.of_strata(strata, world)})
world.rent = {"plain": 300.0, "hills": 200.0}
found = by_key(Sector.of_strata(strata, world))
check("rents that fall form a group of landholders", ("landholders", "owners") in found and ("landholders", "lords") in found, list(found))
check("their loss is their share of the rent that fell away", abs(found[("landholders", "owners")].lost_income - 375.0) < 1e-9,
      found[("landholders", "owners")].lost_income)
world.output = world.output * 0.1
check("a fall in the society's output does not make landholders out of pocket while rents hold",
      by_key(Sector.of_strata(strata, world)).keys() == found.keys())

# ---- workers out of a job -------------------------------------------------------------------------------------------------
registry, world = build()
strata = registry.of_kind("stratum")
world.idle = {"labourer": (10.0, 100.0)}
Sector.remember_welfare(strata, world)
check("hours left unhired as they were organise nobody", all(kind != JOBLESS_WORKERS for kind, _subject in by_key(Sector.of_strata(strata, world))))
world.idle = {"labourer": (40.0, 100.0)}
world.technique = "water_mill"
found = by_key(Sector.of_strata(strata, world))
check("a trade whose hours go unhired more than expected forms a group of jobless workers",
      (JOBLESS_WORKERS, "toilers") in found, list(found))
jobless = found[(JOBLESS_WORKERS, "toilers")]
toilers = registry.actors["stratum:home:toilers"].record
working = toilers.members * STRATUM_WORKING_SHARE
check("the people out of work are the rise in the unhired share of the working people",
      abs(jobless.members - 0.3 * working) < 1e-6 * working, (jobless.members, working))
check("their loss is the pay of those jobs", abs(jobless.lost_income - 0.3 * working * 150.0) < 1e-6 * working * 150.0, jobless.lost_income)
check("the sector names the technique that displaced them", jobless.technique == "water_mill" and "the water_mill" in jobless.cause, jobless.cause)
world.technique = None
check("with no technique to name, the loss is still theirs",
      by_key(Sector.of_strata(strata, world))[(JOBLESS_WORKERS, "toilers")].technique == "")
for _year in range(60):
    Sector.remember_welfare(strata, world)
check("unemployment that lasts becomes the new normal", (JOBLESS_WORKERS, "toilers") not in by_key(Sector.of_strata(strata, world)))

nodes = {"hand_loom": {"cat": "textiles", "lab": {"weaver": 90, "labourer": 10}},
         "mill": {"cat": "textiles", "lab": {"weaver": 20, "labourer": 10, "millwright": 70}},
         "loom_two": {"cat": "textiles", "lab": {"weaver": 80, "labourer": 20}},
         "forge": {"cat": "metal", "lab": {"smith": 100}}}
check("the displacing technique is the newest running one that leans less on the trade than its category does",
      displacing_technique("weaver", {"hand_loom": 1, "mill": 50, "loom_two": 10}, nodes) == "mill")
check("none is named where no running technique leans less on the trade than its category does",
      displacing_technique("weaver", {"hand_loom": 1}, nodes) is None)
check("a technique in another category does not displace the trade", displacing_technique("weaver", {"forge": 5}, nodes) is None)
check("a technique that is not running is not named", displacing_technique("weaver", {}, nodes) is None)

# ---- a church: endowments, tithes, a stipend line -------------------------------------------------------------------
def foundation(cls, kind, **fields):
    defaults = dict(kind=kind, name=kind + " of the realm", members=100.0, stipend_trade="priest", endowment_hectares=500.0,
                    tithe_rate=0.1, tithe_need="food")
    defaults.update(fields)
    return cls("%s:home" % kind, ActorRecord(**defaults))


world = StakeWorld()
church = foundation(Church, "church")
church.advance(world)
check("a church collects the rent of its endowment and a tithe",
      church.record.revenue_by_form == {"endowment": 1000.0, "tithes": 100.0}, church.record.revenue_by_form)
check("it pays its clergy the stipend from what it collected", church.record.need["stipends"] == 20000.0 and church.record.unfunded["stipends"] == 20000.0 - 1100.0,
      (church.record.need, church.record.unfunded, church.money))
check("what it collects is the money it holds less the stipends paid", abs(church.money) < 1e-9, church.money)
Sector.remember_foundations([church])
check("a church that collects what it expected organises nobody", Sector.of_foundations([church]) == [])
world.tithable = 400.0
church.advance(world)
sectors = Sector.of_foundations([church])
check("when a technique takes the goods off the tithed market the clergy form a group",
      len(sectors) == 1 and sectors[0].kind == "clergy" and sectors[0].subject == "church:home", sectors)
check("their loss is the tithe that fell away and their number the clergy it kept",
      abs(sectors[0].lost_income - 60.0) < 1e-9 and sectors[0].members == 100.0, (sectors[0].lost_income, sectors[0].members))
check("the grievance names the source", "tithes" in sectors[0].cause and "60%" in sectors[0].cause, sectors[0].cause)
for _year in range(60):
    Sector.remember_foundations([church])
check("clergy forget a fall that lasts", Sector.of_foundations([church]) == [])

# ---- an academy: scholars, patrons, and the spread of schooling --------------------------------------------------------
world = StakeWorld()
world.strata = [SimpleNamespace(record=SimpleNamespace(members=1000.0, literacy=0.1))]
academy = foundation(Academy, "academy", members=10.0, stipend_trade="scholar", tithe_rate=0.0, endowment_hectares=0.0, patronage_rate=0.8)
academy.advance(world)
check("an academy collects the patronage that pays for learning while few can read",
      abs(academy.record.revenue_by_form["patronage"] - 0.8 * 10.0 * 300.0 * 0.9) < 1e-9, academy.record.revenue_by_form)
Sector.remember_foundations([academy])
world.strata[0].record.literacy = 0.6
academy.advance(world)
sectors = Sector.of_foundations([academy])
check("when schooling spreads and learning is no longer scarce the scholars lose their standing",
      len(sectors) == 1 and sectors[0].kind == "scholars" and "patronage" in sectors[0].cause, sectors)

# ---- the state's office-holders and soldiers --------------------------------------------------------------------------------------
world = StakeWorld()
world.population = 100000.0
government = Government("government:home", ActorRecord(kind="government", army=1000.0))
government.record.need = {"administration": 5000.0, "army": 180000.0}
government.record.unfunded = {"administration": 0.0, "army": 0.0}
group_servants.remember_servants(government, world)
check("a state that pays its way has no unhappy servants", Sector.of_servants(government, world) == [])
government.record.unfunded = {"administration": 2500.0, "army": 90000.0}
world.revenue = 5000.0
found = by_key(Sector.of_servants(government, world))
check("office-holders whose salaries go unpaid and whose fees fall form a group",
      ("office_holders", "administration") in found, list(found))
check("the grievance names the salaries and the fees", "salaries" in found[("office_holders", "administration")].cause
      and "fees" in found[("office_holders", "administration")].cause, found[("office_holders", "administration")].cause)
check("soldiers whose line goes half unpaid form a group whose loss is the arrears",
      abs(found[("soldiers", "army")].lost_income - 90000.0) < 1e-9 and abs(found[("soldiers", "army")].members - 500.0) < 1e-9,
      (found[("soldiers", "army")].lost_income, found[("soldiers", "army")].members))

check("an army that is paid keeps its loyalty", group_servants.step_loyalty(1.0, 0.0) == 1.0)
check("an army that goes unpaid loses it", group_servants.step_loyalty(1.0, 0.5) < 1.0)
loyal = group_servants.mutiny(0.9, 1000.0, 5000.0, 100000.0)
check("a loyal army does nothing to the state", loyal["deserters"] == 0.0 and loyal["seized"] == 0.0)
restless = group_servants.mutiny(0.2, 1000.0, 5000.0, 100000.0)
check("an army that has lost its loyalty deserts and takes its arrears from the treasury",
      restless["deserters"] > 0.0 and restless["seized"] > 0.0, restless)
check("a worse loyalty does worse to the state", group_servants.mutiny(0.0, 1000.0, 5000.0, 100000.0)["deserters"] > restless["deserters"])
check("it cannot take more than the treasury holds", group_servants.mutiny(0.0, 1000.0, 5000.0, 10.0)["seized"] == 10.0)
for _year in range(6):
    government.record.loyalty = group_servants.step_loyalty(government.record.loyalty, 0.5)
government.money = 50000.0
before_army = government.record.army
acted = group_servants.run_army_year(government, world)
check("a year of mutiny cuts the army and empties the treasury of the arrears taken",
      government.record.army < before_army and acted["seized"] > 0.0 and government.money < 50000.0
      and any("MUTINY" in line for line in world.said), (government.record.army, government.money, world.said))

# ---- a prohibition reaches a technique through substitutes ----------------------------------------------------------------------
tree = {"steel_plant": {"cat": "metal", "pre": []}, "bronze_foundry": {"cat": "metal", "pre": []}}
makes = {"steel_plant": ["steel_kg"], "bronze_foundry": ["bronze_kg"]}
substitutes = {"steel_kg": ["bronze_kg"], "bronze_kg": ["steel_kg"]}
plain_reach = subjects_reached("steel_plant", tree, lambda node_id: makes[node_id], lambda material: material)
check("without substitutes a technique reaches what it makes", "bronze_kg" not in plain_reach and "steel_kg" in plain_reach)
wide_reach = subjects_reached("steel_plant", tree, lambda node_id: makes[node_id], lambda material: material,
                              lambda material: substitutes.get(material, ()))
check("with substitutes it also reaches the producers of what its goods replace", "bronze_kg" in wide_reach, wide_reach)
check("workers out of a job can obtain a prohibition, like producers", JOBLESS_WORKERS in BANNING_KINDS)
strong = state_response(0.9, 0.9, False, JOBLESS_WORKERS, 100.0, 1000.0)
check("a state not in deficit forbids the technique that took their jobs", strong["ban"])
check("a state in deficit compensates instead", not state_response(0.9, 0.9, True, JOBLESS_WORKERS, 100.0, 1000.0)["ban"])
check("a church cannot obtain a prohibition, only be made good", not state_response(0.9, 0.9, False, "clergy", 100.0, 1000.0)["ban"])


class GroupWorld(StakeWorld):
    def __init__(self):
        super().__init__()
        self.sector_table = {}
        self.blamed = []

    def sectors(self):
        return self.sector_table

    def scope_revenue(self, scope):
        return 10000.0 * scope

    def concession_paid(self, line_name):
        return 0.0

    def state_in_deficit(self):
        return False

    def state_capacity(self):
        return 0.9

    def founder_protection(self):
        return 0.0

    def lodge_blame(self, amount, text, year_gap, group_record):
        self.blamed.append(text)


state = ActorsState(home_country="home")
registry = ActorRegistry(state)
group_world = GroupWorld()
jobless_sector = Sector(JOBLESS_WORKERS, "toilers", "the toilers (out of work)", "30% of the hours go unhired", 5000.0, 20000.0, 400.0, 1.0,
                        technique="water_mill")
group_world.sector_table = {"jobless_workers:toilers": jobless_sector}
formed = registry.consider_groups(group_world)
group = registry.actors["group:jobless_workers:toilers"]
check("workers out of a job organise as a group that remembers the technique", formed == ["group:jobless_workers:toilers"]
      and group.record.technique == "water_mill", (formed, group.record.technique))
check("the group asks the state to ban that technique, not a commodity",
      any("fewer hands" in demand for demand in group.record.demands), group.record.demands)
check("a commodity prohibition is not made of it", registry.prohibitions() == {})
check("the petition's words name the cause", "hours go unhired" in group.words(group_world), group.words(group_world))

# ---- the economy's labour clearing keeps the hours it left unhired -----------------------------------------------------------------
from sim.economy.api import country_figures
from sim.economy.setup import labour_area
from sim.economy.market_memory import market_key

economy = SimpleNamespace(setup=SimpleNamespace(tiles=["t1", "t2"]),
                          record=SimpleNamespace(hours_idle={market_key("weaver", labour_area("t1")): 30.0, market_key("weaver", labour_area("t2")): 10.0},
                                                 hours_hired={market_key("weaver", labour_area("t1")): 70.0, market_key("weaver", labour_area("t2")): 90.0}))
idle = country_figures.idle_hours_by_trade(economy, None)
check("the idle hours of a trade are summed over its markets, with the hours offered", idle == {"weaver": (40.0, 200.0)}, idle)

from sim.economy.record import EconomyRecord
check("the record keeps the idle hours through a save", "hours_idle" in EconomyRecord.__dataclass_fields__)

# ---- goods that serve the same need substitute for one another -----------------------------------------------------------------------
from sim.engine import need_substitutes
check("goods that serve the same need are substitutes", "maize_kg" in need_substitutes.substitutes_of("wheat_kg"))
check("a good is not its own substitute", "wheat_kg" not in need_substitutes.substitutes_of("wheat_kg"))
check("the goods that serve one need are listed", "wheat_kg" in need_substitutes.serving("food"))
check("a good no need names has no substitutes", need_substitutes.substitutes_of("nothing_at_all") == frozenset())

# ---- a civilisation's data founds its church and academy ---------------------------------------------------------------------------------
import glob
import json
import os

from .harness import ROOT
from sim.agents.api import cast_from_civilisations, seed_cast

for path in sorted(glob.glob(os.path.join(ROOT, "data", "civilizations", "[a-z]*_[0-9]*.json"))):
    with open(path) as handle:
        civilisation = json.load(handle)
    home, entries, profiles = cast_from_civilisations(civilisation, [])
    cast_registry = ActorRegistry(ActorsState())
    seed_cast(cast_registry, home, entries, profiles)
    church_actor = cast_registry.actors.get("church:home")
    check("%s starts with a church that keeps people on endowed land" % home,
          church_actor is not None and church_actor.kind == "church" and church_actor.record.members > 0.0
          and church_actor.record.endowment_hectares > 0.0 and church_actor.record.stipend_trade, church_actor)
    check("%s's civilisation file says where its starting church and academy come from" % home,
          civilisation["_internal"]["cast_actors"]["source"] and civilisation["_internal"]["cast_actors"]["confidence"] in "ABCD")
