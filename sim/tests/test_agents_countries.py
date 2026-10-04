"""Countries as actors: profiles and the cast from civilisation dicts, seeding, a country's own world, a foreign government."""
from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, RecordedActor
from sim.agents import registry as registry_module
from sim.agents import country_view, government_foreign  # noqa: F401  (they register themselves)
from sim.agents.cast import cast_from_civilisations, profile_from_civilisation, seed_cast
from sim.agents.country_view import CountryWorld
from sim.agents.protocols import World
from sim.engine.state import deserialize_state, serialize_state

from .agents_fake_world import FakeWorld, make_node, total_money


class ScenarioWorld(FakeWorld):
	"""The shared (home) world plus what a country's scope asks of it."""

	def __init__(self) -> None:
		super().__init__()
		self.pay = {"labourer": 100.0, "soldier": 120.0, "scribe": 150.0}
		self.weights = {"military": 1.0}
		self.distances = {}

	def pay_per_person_year(self, trade):
		return self.pay[trade]

	def state_weights(self):
		return dict(self.weights)

	def distance_km(self, place_a, place_b):
		return self.distances.get(place_a, 0.0)

	def exposure(self, node_id, location):
		return 1.0


class Observer(RecordedActor):
	"""A stand-in for a declared extra actor (a second player)."""
	kind = "observer"


registry_module.register_actor_kind("observer", Observer)

# ---- profiles from civilisation dicts ---------------------------------------------------
bare = profile_from_civilisation({"id": "alpha"})
check("a civilisation with almost nothing in it still gives a profile",
	  bare.country == "alpha" and bare.name == "alpha" and bare.population == 0.0 and bare.location is None
	  and bare.starting_techs == set() and bare.wage_index == 1.0 and bare.strata == [], bare)
HOME = {"id": "alpha", "name": "Alpha", "population": 1_000_000, "urban_fraction": 0.1, "state_capacity": 0.8,
		"starting_tax_share": 0.1, "wage_index": 1.0, "price_index": 1.0, "literacy_general": 0.2, "literacy_elite": 0.9,
		"home_regions": ["north", "south"], "starting_techs": ["plough", "wheel"], "standing_army": 5000,
		"values": {"w_military": 0.9},
		"cast": {"strata": [{"name": "farmers", "share": 0.9}], "treasury": 50.0, "mood": "calm",
				 "actors": [{"actor_id": "observer:1", "kind": "observer", "controller": "llm", "money": 20.0,
							 "knowledge": ["wheel"]}]}}
BETA = {"id": "beta", "name": "Beta", "population": 500_000, "state_capacity": 0.5, "starting_tax_share": 0.2,
		"wage_index": 0.5, "home_regions": ["east"], "starting_techs": ["loom"], "cast": {"treasury": 10.0, "countries": [
			{"id": "gamma", "name": "Gamma", "population": 100_000, "starting_techs": ["raft"], "home_regions": ["isles"]}]}}
DELTA = {"id": "delta", "population": 200_000}
profile = profile_from_civilisation(HOME)
check("a profile reads the civilisation's own fields",
	  profile.population == 1_000_000 and profile.tax_share == 0.1 and profile.starting_techs == {"plough", "wheel"}
	  and profile.location == "north" and profile.home_regions == ["north", "south"], profile)
check("a profile carries strata from the cast key and keeps unconsumed cast keys in extra",
	  profile.strata == [{"name": "farmers", "share": 0.9}] and profile.extra.get("mood") == "calm"
	  and "treasury" not in profile.extra and "actors" not in profile.extra, profile.extra)
check("a profile keeps the army and values the civilisation declares",
	  profile.extra["standing_army"] == 5000 and profile.extra["values"] == {"w_military": 0.9})

# ---- the cast of a three-country game ---------------------------------------------------
home_country, entries, profiles = cast_from_civilisations(HOME, [BETA, DELTA])
by_id = {entry.actor_id: entry for entry in entries}
check("the home country is the home civilisation's", home_country == "alpha")
check("every country has a profile, declared ones too", set(profiles) == {"alpha", "beta", "gamma", "delta"}, set(profiles))
check("the home government is a government with no foreign country",
	  by_id["government:alpha"].kind == "government" and by_id["government:alpha"].country is None
	  and by_id["government:alpha"].money == 50.0)
check("each foreign country has a foreign government of its own",
	  all(by_id["government:" + country].kind == "foreign_government" and by_id["government:" + country].country == country
		  for country in ("beta", "gamma", "delta")))
check("a government sits where its country is", by_id["government:beta"].location == "east")
check("a declared actor joins the cast with its own fields",
	  by_id["observer:1"].kind == "observer" and by_id["observer:1"].controller == "llm"
	  and by_id["observer:1"].money == 20.0 and by_id["observer:1"].params == {"knowledge": ["wheel"]}
	  and by_id["observer:1"].country is None, by_id.get("observer:1"))
check("no entry exists beyond the countries' governments and the declared actors", len(entries) == 5, sorted(by_id))
_home_only, alone, _profiles = cast_from_civilisations({"id": "solo"}, [])
check("a lone civilisation is a cast of one government", [entry.actor_id for entry in alone] == ["government:solo"])

# ---- seeding ----------------------------------------------------------------------------
state = ActorsState()
registry = ActorRegistry(state)
created = seed_cast(registry, home_country, entries, profiles)
check("seeding creates a record per entry", set(created) == set(by_id) and set(registry.actors) == set(by_id), created)
check("seeding sets the home country and stores the roster",
	  state.home_country == "alpha" and set(state.cast) == set(by_id) and set(state.countries) == set(profiles))
check("a foreign government's opening money is booked as an edge",
	  registry.actors["government:beta"].money == 10.0
	  and registry.actors["government:beta"].record.income == {"edge:opening": 10.0})
check("a declared actor's fields reach its record",
	  registry.actors["observer:1"].record.controller == "llm" and registry.actors["observer:1"].record.knowledge == {"wheel"}
	  and registry.actors["observer:1"].money == 20.0)
registry.actors["government:beta"].debit(3.0, "edge:test")
check("seeding twice creates nothing and leaves existing actors alone",
	  seed_cast(registry, home_country, entries, profiles) == [] and registry.actors["government:beta"].money == 7.0)
loaded = deserialize_state(serialize_state(state), ActorsState)
reloaded = ActorRegistry(loaded)
check("the roster survives save and load and seeds nothing new",
	  seed_cast(reloaded, home_country, entries, profiles) == [] and set(reloaded.actors) == set(by_id)
	  and loaded.countries["beta"].starting_techs == {"loom"} and loaded.cast["observer:1"].params == {"knowledge": ["wheel"]})
check("an entry of a kind not yet registered waits in the roster",
	  seed_cast(reloaded, home_country, [type(entries[0])(actor_id="x:1", kind="not_yet_a_kind")], {}) == []
	  and "x:1" in loaded.cast and "x:1" not in reloaded.actors)

# ---- what a country sees ----------------------------------------------------------------
world = ScenarioWorld()
world.baseline = {"shared_tech"}
world.nodes["wheel"] = make_node("wheel")
home_actor = registry.actors["government:alpha"]
beta_actor = registry.actors["government:beta"]
check("a country's scope is registered", registry_module.WORLD_SCOPE[0] is not None)
check("a home actor sees the shared world", registry.world_for(home_actor, world) is world)
beta_world = registry.world_for(beta_actor, world)
check("a foreign actor sees its country's world", isinstance(beta_world, CountryWorld) and beta_world.civ_id == "beta")
check("a foreign actor's baseline tree is its own country's techniques",
	  beta_world.baseline_knowledge() == {"loom"} and beta_actor.knows("loom", beta_world)
	  and not beta_actor.knows("shared_tech", beta_world))
check("a home actor's baseline tree is the shared world's", home_actor.knows("shared_tech", world))
check("a country answers for its own people and state",
	  beta_world.population_total() == 500_000 and beta_world.state_capacity() == 0.5
	  and beta_world.urban_population() == 0.0 and beta_world.tax_share() == 0.2)
check("a country's wages are scaled by its wage level against the home country's",
	  beta_world.pay_per_person_year("labourer") == 50.0
	  and CountryWorld(world, profiles["alpha"], registry).pay_per_person_year("labourer") == 100.0)
home_view = CountryWorld(world, profiles["alpha"], registry)
check("a country with declared values weighs inventions by them",
	  home_view.state_weights()["military"] == 0.9 and beta_world.state_weights() == {"military": 1.0})
own_view = CountryWorld(world, profiles["beta"], registry)
check("a country's government is its own actor in the registry", own_view.government() is beta_actor)
beta_firm = registry.add("firm:beta", ActorRecord(kind="firm", country="beta", money=100.0))
beta_purse = beta_actor.money
taken = registry.world_for(beta_firm, world).government().collect(beta_firm, 100.0, beta_world)
check("a foreign state levies a firm of its own country at its tax share and capacity, money moving across",
	  abs(taken - 100.0 * 0.2 * 0.5) < 1e-9 and abs(beta_firm.money - (100.0 - taken)) < 1e-9
	  and abs(beta_actor.money - (beta_purse + taken)) < 1e-9, (taken, beta_firm.money, beta_actor.money))
world.rate = 0.07
check("an arbitrary shared member passes straight through", beta_world.market_rate() == 0.07)
check("shared attributes pass through as properties",
	  beta_world.year == world.year and beta_world.hours_per_person_year == 2000.0 and beta_world.labour_market is world.labour_market)
check("shared randomness passes through", beta_world.rng_for(1, "x").random() == world.rng_for(1, "x").random())
check("every member of the World protocol is answered by a country's world",
	  all(hasattr(CountryWorld, name) for name in vars(World) if not name.startswith("_")))
check("forwarding is explicit, not by __getattr__", "__getattr__" not in vars(CountryWorld))

# ---- fog: the farther the country, the less it learns -------------------------------------
world.distances = {"east": 100.0, "isles": 4000.0}
near = CountryWorld(world, profiles["beta"], registry).exposure("wheel", None)
far = CountryWorld(world, profiles["gamma"], registry).exposure("wheel", None)
check("a nearer country gets more exposure than a farther one", 0.0 < far < near < 1.0, (near, far))
check("an observer's own place counts when it is given",
	  CountryWorld(world, profiles["beta"], registry).exposure("wheel", "isles") == far)

# ---- a foreign government's year ----------------------------------------------------------
world.demonstrated_nodes = {"wheel"}
world.nodes["wheel"] = make_node("wheel", hours=100.0, years=1.0)
world.nodes["wheel"]["gains"] = {"military": 1000.0}
state2 = ActorsState()
registry2 = ActorRegistry(state2)
seed_cast(registry2, "alpha", [entry for entry in entries if entry.actor_id == "government:beta"], profiles)
government = registry2.actors["government:beta"]
world.distances = {"east": 0.0}
registry2.advance(world)
income, outlays = government.record.income, government.record.outlays
check("a foreign government raises revenue from its country's taxpayers",
	  income.get("edge:foreign_taxpayers", 0.0) > 0.0, income)
expected = 500_000 * 0.3 * 50.0 * 0.2 * 0.5
check("its revenue follows from people, wages, tax share and capacity",
	  abs(income["edge:foreign_taxpayers"] - expected) < 1e-6, (income, expected))
check("it spends on its army and officials", outlays.get("edge:foreign_payroll_army", 0.0) > 0.0
	  and outlays.get("edge:foreign_payroll_officials", 0.0) > 0.0, outlays)
check("its purse is its income less its outlays, opening money included",
	  abs(government.money - (sum(income.values()) - sum(outlays.values()))) < 1e-6, government.money)
check("money enters and leaves a foreign government only at named edges or on its own copying",
	  all(label.startswith("edge:") or label == "copying" for label in list(income) + list(outlays)), (income, outlays))
check("it keeps what it does not spend", government.money > 0.0)
check("it never levies the founder's side of the world", world.government_actor.asked == [])
check("it copies the founder's invention it values, from its own tree",
	  "wheel" in government.knowledge or "wheel" in government.works, (government.knowledge, government.works))
check("its staff stay out of the founder's labour pool", government.workforce == {})
check("a foreign government's army follows its funded share", government.record.army > 0.0)

# nothing beyond the world a government is not given: a country with no wage gets no revenue, no crash
poor = CountryWorld(world, profiles["gamma"], registry2)
check("a world that is not a country's scope yields a government no revenue", government.revenue(world) == 0.0)
check("revenue scales with a country's taxable people",
	  government.revenue(own_view) > government.revenue(poor), (government.revenue(own_view), government.revenue(poor)))
check("every actor's money other than the foreign government's is untouched", total_money(
	[actor for actor_id, actor in registry2.actors.items() if actor_id != "government:beta"]) == 0.0)
