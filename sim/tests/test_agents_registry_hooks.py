"""The actor registry is open to new kinds, spawners and country scopes through its extensions, and the roster saves."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CastEntry, CountryProfile, RecordedActor, combine_extensions, shipped_extensions
from sim.engine.state import deserialize_state, serialize_state

from .agents_fake_world import FakeWorld


class Dragon(RecordedActor):
	"""A mod's actor kind: it eats its purse a little every year."""
	kind = "dragon"

	def act(self, world):
		self.debit(1.0, "upkeep")


extensions = shipped_extensions()
extensions.kinds["dragon"] = Dragon
state = ActorsState(home_country="home")
registry = ActorRegistry(state, extensions)
dragon = registry.add("dragon:1", ActorRecord(kind="dragon", money=10.0))
check("a registered kind builds its own class", isinstance(dragon, Dragon))

hatched = []


def hatch(registry, world):
	if "dragon:2" in registry.actors:
		return []
	registry.add("dragon:2", ActorRecord(kind="dragon", money=5.0))
	hatched.append(world.year)
	return ["dragon:2"]


extensions.spawners.append(("test_hatchery", hatch))
world = FakeWorld()
registry.advance(world)
check("a provided kind takes its yearly turn", dragon.money == 9.0, dragon.money)
check("a provided spawner runs after the actors' turns", "dragon:2" in registry.actors and hatched == [world.year])
combined = combine_extensions([], [[("test_hatchery", hatch)], [("other", hatch)], [("test_hatchery", lambda registry, world: [])]], None, [], [])
names = [name for name, _spawner in combined.spawners]
check("providing a spawner name again replaces it in place", names == ["test_hatchery", "other"], names)
check("the shipped spawners include the firm entry and the interest groups",
	  {"firm_entry", "interest_groups"} <= {name for name, _spawner in shipped_extensions().spawners})

# ---- an actor of another country sees its country's world --------------------------------
state.countries["far"] = CountryProfile(country="far", name="Far", starting_techs={"plough"})
foreign = registry.add("dragon:far", ActorRecord(kind="dragon", country="far"))
check("an actor with no country answers to the home country", registry.country_of(dragon) == "home")
check("an actor's own country is its country", registry.country_of(foreign) == "far")
extensions.world_scope = None
registry._scoped = {}
check("with no scope provided every actor sees the shared world", registry.world_for(foreign, world) is world)
extensions.world_scope = lambda shared, profile, actors_state: ("scoped", profile.country)
check("a home actor still sees the shared world", registry.world_for(dragon, world) is world)
registry._scoped = {}
check("a foreign actor sees its country's scope", registry.world_for(foreign, world) == ("scoped", "far"))

# ---- the roster and countries round-trip through the save ---------------------------------
saved = ActorsState(home_country="home")
saved.countries["far"] = CountryProfile(country="far", population=1000.0, starting_techs={"plough"},
													strata=[{"name": "farmers", "share": 0.9}])
saved.cast["government:far"] = CastEntry(actor_id="government:far", country="far", money=3.0)
saved.records["player:2"] = ActorRecord(kind="player", controller="llm", country="far",
													orders=[{"command": "research", "node": "plough"}])
loaded = deserialize_state(serialize_state(saved), ActorsState)
check("a country profile survives save and load",
	  loaded.countries["far"].starting_techs == {"plough"} and loaded.countries["far"].strata[0]["name"] == "farmers")
check("the cast survives save and load", loaded.cast["government:far"].money == 3.0 and loaded.home_country == "home")
check("a player's queued orders survive save and load",
	  loaded.records["player:2"].orders == [{"command": "research", "node": "plough"}]
	  and loaded.records["player:2"].controller == "llm")

# ---- review regressions: any exited actor rests; firm ids never collide ------------------------
resting = ActorRegistry(ActorsState(home_country="home"), extensions)
gone = resting.add("dragon:gone", ActorRecord(kind="dragon", money=10.0, exited_year=99))
resting.advance(FakeWorld())
check("an exited actor of any kind takes no more turns", gone.money == 10.0, gone.money)
crowded = ActorRegistry(ActorsState(home_country="home"))
crowded.add("firm:2", ActorRecord(kind="firm", money=1.0, target="kept"))
entry_world = FakeWorld()
entry_world.proven = {"mill"}
entry_world.nodes["mill"] = {"id": "mill", "pre": [], "lab": {"labourer": 10.0}, "yrs": 1.0, "rev": 1.0e6, "up": 0.0}
entry_world.demonstrated_nodes = {"mill"}
entry_world.entry_gross = lambda node_id, rivals, entrants: 1.0e6
entry_world.concern_wage_bill = lambda node_id, capacity=1.0: 0.0
founded = crowded.consider_entry(entry_world)
check("a new firm never takes an id already in use", founded and crowded.get("firm:2").record.target == "kept"
	  and "firm:2" not in founded, founded)
