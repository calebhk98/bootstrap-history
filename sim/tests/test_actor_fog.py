"""Complaint 103: fog of war for actors. A firm, an entrant or a state copies only what it can see enough of from
where it stands: a kept secret, an opaque technique or a faraway maker shows too little to copy."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import imitation

from .agents_fake_world import FakeWorld, make_node


class SightWorld(FakeWorld):
	"""How much of each invention shows at an observer's place is set per node and place."""

	def __init__(self):
		super().__init__()
		self.shows = {}

	def exposure(self, node_id, location):
		return self.shows.get((node_id, location), self.shows.get(node_id, 1.0))

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step


def make_world(shows):
	world = SightWorld()
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
	world.demonstrated_nodes = {"shop"}
	world.proven = {"shop"}
	world.shows["shop"] = shows
	return world


check("enough showing is sight", imitation.in_sight("tile", "shop", make_world(0.9)))
check("too little showing is not", not imitation.in_sight("tile", "shop", make_world(0.1)))
world = make_world(1.0)
world.shows[("shop", "far")] = 0.05
check("the same invention is seen from near and not from far", imitation.in_sight("near", "shop", world) and not imitation.in_sight("far", "shop", world))

# ---- a firm aiming at a concern it cannot see does not start copying it ------------------------------------
for shows, expected in ((0.9, True), (0.1, False)):
	world = make_world(shows)
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", money=1.0e6, target="shop", founded_year=0, last_margin=5000.0))
	world.baseline = set()
	options = firm.imitation_options(world)
	check("a firm copies a target it sees (%s) or cannot (%s)" % (expected, not expected), bool(options) == expected, (shows, options))

# ---- an entrant founds into a niche only where it can see the proven concern ------------------------------
for shows, expected in ((0.9, True), (0.1, False)):
	world = make_world(shows)
	registry = ActorRegistry(ActorsState(home_country="home"))
	founded = registry.consider_entry(world)
	check("entry follows sight: shows %.1f founds %s" % (shows, expected), bool(founded) == expected, (shows, founded))
