"""Complaint 103: a live patent held by another actor stops a firm from entering a concern and an
actor from copying an invention, until the holder licenses it or the term ends."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import patent
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld, make_node


class EntryWorld(FakeWorld):
	"""A world whose proven concern pays one entrant its takings shared among the sellers."""

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step


class PatentedEntryWorld(EntryWorld):
	registry = None

	def patent_entry(self, node_id):
		return patent.entry_among(self.registry.actors.values(), node_id, self.year)


def make_world():
	world = PatentedEntryWorld()
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
	world.demonstrated_nodes = {"shop"}
	world.proven = {"shop"}
	world.registry = ActorRegistry(ActorsState(home_country="home"))
	world.registry.add("stratum:home:merchants", ActorRecord(
		kind="stratum", stratum="merchants", members=100.0, money=1.0e6, literacy=0.5))
	return world


def patented(world):
	holder = world.registry.add("player:holder", ActorRecord(kind="player", money=10.0, controller="human"))
	holder.record.patents["shop"] = {"granted": world.year, "expires": world.year + 10, "licensees": []}
	return holder


# ---- firm entry
world = make_world()
check("an unpatented concern draws an entrant", len(world.registry.consider_entry(world)) == 1)

world = make_world()
patented(world)
check("a live patent held by another actor bars firm entry", world.registry.consider_entry(world) == [])

world.year += 11
check("an expired patent no longer bars entry", len(world.registry.consider_entry(world)) == 1)

# ---- imitation
world = make_world()
copier = world.registry.add("firm:copier", ActorRecord(kind="firm", money=1.0e6, founded_year=0, target="shop", last_margin=1000.0))
world.founder_inventions = lambda: ["shop"]
unpatented_options = copier.imitation_options(world)
holder = patented(world)
check("an invention is offered to copy while unpatented", [each.subject for each in unpatented_options] == ["shop"],
	unpatented_options)
check("a live patent held by another actor removes the copy option", copier.imitation_options(world) == [])
holder.record.patents["shop"]["licensees"].append("firm:copier")
check("a licensee may copy a patented invention", [each.subject for each in copier.imitation_options(world)] == ["shop"])
