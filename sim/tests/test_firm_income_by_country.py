"""Complaint 649: a firm's taxable income is split among the countries its operating plants stand in, by what each took, and
each state sees the part earned on its own tiles. The rules are called on built inputs and stand-ins."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents import taxpayer_income
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CastEntry, CountryProfile, CountryWorld, Firm, seed_cast
from sim.agents.business import Business
from sim.agents.business_plant import MOTHBALLED

from .country_state_world import StateWorld

OWNERS = {"home_tile": "home", "far_tile": "far"}
split = taxpayer_income.income_by_country

check("a firm with no plant earns where it answers", split(10.0, [], "home", OWNERS.get) == {"home": 10.0})
check("a plant with no tile, or on a tile no country holds, earns where the firm answers",
	  split(10.0, [(None, 5.0), ("sea", 5.0)], "home", OWNERS.get) == {"home": 10.0})
shares = split(12.0, [("home_tile", 3.0), ("far_tile", 1.0)], "home", OWNERS.get)
check("the income is split by what each plant took, by the country of its tile", shares == {"home": 9.0, "far": 3.0}, shares)
check("the parts add up to the income", abs(sum(shares.values()) - 12.0) < 1e-9)
check("plants that took nothing split it equally", split(12.0, [("home_tile", 0.0), ("far_tile", 0.0)], "home", OWNERS.get) == {"home": 6.0, "far": 6.0})
check("two plants in one country add up there", split(12.0, [("far_tile", 1.0), ("far_tile", 1.0)], "home", OWNERS.get) == {"far": 12.0})

business = Business()
business.open_plant("mill", 100, "far_tile")
business.open_plant("forge", 100)
check("a plant keeps the tile it was opened on, and none when none was named",
	  business.plant_of("mill").tile == "far_tile" and business.plant_of("forge").tile is None)


def firm(margin, country=None, plants=()):
	found = Business()
	for tile, takings in plants:
		found.open_plant("plant%d" % len(found.plants), 100, tile).takings = takings
	return SimpleNamespace(record=SimpleNamespace(country=country, last_margin=margin, business=found))


firms = [firm(20.0), firm(8.0, plants=[("home_tile", 1.0), ("far_tile", 3.0)]), firm(4.0, "far"), firm(-5.0, plants=[("far_tile", 1.0)])]
country_of = lambda each: each.record.country or "home"
at_home = taxpayer_income.firm_incomes_in(firms, "home", country_of, OWNERS.get)
abroad = taxpayer_income.firm_incomes_in(firms, "far", country_of, OWNERS.get)
check("the home state sees the home part of each firm with a plant there, and a firm with none placed",
	  [income for _firm, income in at_home] == [20.0, 2.0], [income for _firm, income in at_home])
check("a foreign state sees the part earned on its tiles, and the firm that answers to it",
	  [income for _firm, income in abroad] == [6.0, 4.0, 0.0], [income for _firm, income in abroad])
check("a loss is taxable as nothing", abroad[-1][1] == 0.0)
mothballed = firm(9.0, plants=[("far_tile", 1.0)])
mothballed.record.business.mothball("plant0", 101, "idle")
check("a plant switched off earns nowhere: the firm earns where it answers",
	  [income for _firm, income in taxpayer_income.firm_incomes_in([mothballed], "home", country_of, OWNERS.get)] == [9.0])
check("the tiles each profile holds say whose a tile is",
	  taxpayer_income.tile_owners({"home": CountryProfile(country="home", home_tiles=["a", "b"]), "far": CountryProfile(country="far", home_tiles=["c"])})
	  == {"a": "home", "b": "home", "c": "far"})


# ---- the foreign state's own view, through a registry --------------------------------------------
def country_world():
	registry = ActorRegistry(ActorsState(home_country="home"))
	entry = CastEntry(actor_id="government:far", country="far", kind="government", money=1.0, params={})
	seed_cast(registry, "home", [entry], {"home": CountryProfile(country="home", home_tiles=["home_tile"]),
										  "far": CountryProfile(country="far", population=24000.0, home_tiles=["far_tile"])})
	return CountryWorld(StateWorld(), registry.state.countries["far"], registry), registry


world, registry = country_world()
check("the registry says whose a tile is", registry.country_of_tile("far_tile") == "far" and registry.country_of_tile("home_tile") == "home"
	  and registry.country_of_tile("sea") is None)
traveller = registry.add("firm:1", ActorRecord(kind="firm", name="traveller", last_margin=8.0, founded_year=100))
traveller.business.open_plant("mill", 100, "home_tile").takings = 1.0
traveller.business.open_plant("forge", 100, "far_tile").takings = 3.0
incomes = [income for _scale, income in world.visible_taxpayers()]
check("a foreign state's visible taxpayers include a home firm for the part its plants earn on the state's tiles", incomes == [6.0], incomes)
