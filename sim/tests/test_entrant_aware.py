"""An entrant is founded into a concern it has seen prove profitable, so it is aware that the technique exists; without
that it could never copy the concern it was founded to run (awareness.py)."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import awareness
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld, make_node


class EntryWorld(FakeWorld):
	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step

	def ramp(self, opened_year, node_id=None):
		return min(1.0, (self.year - opened_year + 1) / 5.0)


world = EntryWorld()
world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
world.demonstrated_nodes = {"shop"}
world.proven = {"shop"}
registry = ActorRegistry(ActorsState(home_country="home"))
registry.add("stratum:home:merchants", ActorRecord(kind="stratum", stratum="merchants", members=100.0, money=1.0e6, literacy=0.5))
founded = registry.consider_entry(world)
check("a firm is founded into the proven concern", bool(founded), founded)
entrant = registry.actors[founded[0]]
check("the entrant is aware of the concern it was founded into",
      awareness.knows_it_exists(entrant, "shop", world) and "shop" in entrant.aware, entrant.aware)
