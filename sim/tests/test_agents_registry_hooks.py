"""The actor registry is open to new kinds, spawners and country scopes, and the roster saves."""
from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, CastEntry, CountryProfile, RecordedActor
from sim.agents import registry as registry_module
from sim.engine.state import deserialize_state, serialize_state

from .agents_fake_world import FakeWorld


class Dragon(RecordedActor):
	"""A mod's actor kind: it eats its purse a little every year."""
	kind = "dragon"

	def act(self, world):
		self.debit(1.0, "upkeep")


registry_module.register_actor_kind("dragon", Dragon)
state = ActorsState(home_country="home")
registry = ActorRegistry(state)
dragon = registry.add("dragon:1", ActorRecord(kind="dragon", money=10.0))
check("a registered kind builds its own class", isinstance(dragon, Dragon))

hatched = []


def hatch(registry, world):
	if "dragon:2" in registry.actors:
		return []
	registry.add("dragon:2", ActorRecord(kind="dragon", money=5.0))
	hatched.append(world.year)
	return ["dragon:2"]


registry_module.register_spawner("test_hatchery", hatch)
world = FakeWorld()
try:
	registry.advance(world)
	check("a registered kind takes its yearly turn", dragon.money == 9.0, dragon.money)
	check("a registered spawner runs after the actors' turns", "dragon:2" in registry.actors and hatched == [world.year])
	registry_module.register_spawner("test_hatchery", lambda registry, world: [])
	names = [name for name, _spawner in registry_module.SPAWNERS]
	check("registering a spawner name again replaces it", names.count("test_hatchery") == 1, names)
	check("the built-in spawners stay registered", {"firm_entry", "interest_groups"} <= set(names), names)
finally:
	registry_module.SPAWNERS[:] = [entry for entry in registry_module.SPAWNERS if entry[0] != "test_hatchery"]

# ---- an actor of another country sees its country's world --------------------------------
state.countries["far"] = CountryProfile(country="far", name="Far", starting_techs={"plough"})
foreign = registry.add("dragon:far", ActorRecord(kind="dragon", country="far"))
check("an actor with no country answers to the home country", registry.country_of(dragon) == "home")
check("an actor's own country is its country", registry.country_of(foreign) == "far")
previous_scope = registry_module.WORLD_SCOPE[0]
try:
	registry_module.WORLD_SCOPE[0] = None
	registry._scoped = {}
	check("with no scope registered every actor sees the shared world", registry.world_for(foreign, world) is world)
	registry_module.register_world_scope(lambda shared, profile, actors_state: ("scoped", profile.country))
	check("a home actor still sees the shared world", registry.world_for(dragon, world) is world)
	registry._scoped = {}
	check("a foreign actor sees its country's scope", registry.world_for(foreign, world) == ("scoped", "far"))
finally:
	registry_module.WORLD_SCOPE[0] = previous_scope

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
