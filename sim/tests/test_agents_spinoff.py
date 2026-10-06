"""Spin-offs: staff who know a concern leave to found a rival firm that copies it; the chance grows with
staff and years, the parent keeps what it knew, the stake is pooled capital, and a patent blocks it."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import exchange_commands, player, spinoff  # noqa: F401
from sim.agents import registry as registry_module

from .agents_fake_world import FakeWorld, make_node


class SpinWorld(FakeWorld):
	patent = None

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id].get("rev", 0.0)) / (1.0 + rivals + entrants)

	def patent_entry(self, node_id):
		return self.patent

	def proof_years(self, node_id):
		return 0.0


def make_world():
	world = SpinWorld(year=100)
	world.baseline = {"base"}
	world.nodes["base"] = make_node("base")
	world.nodes["gear"] = make_node("gear", ["base"])
	world.nodes["mill"] = make_node("mill", ["gear"], hours=100.0, revenue=2000.0)
	world.output = 1.0e9
	return world


def make_parent(kind="firm", staff=500.0):
	registry = ActorRegistry(ActorsState(home_country="home"))
	parent = registry.add("firm:1" if kind == "firm" else "player:p", ActorRecord(kind=kind, money=1000.0, founded_year=50))
	parent.knowledge.update({"gear", "mill"})
	parent.concerns.add("mill")
	parent.record.opened_year["mill"] = 80
	parent.workforce["labourer"] = staff
	return registry, parent


world = make_world()
registry, parent = make_parent()
check("the spawner is registered", "spinoffs" in dict(registry_module.SPAWNERS))

# ---- the chance: staff and years --------------------------------------------------------------------
few = spinoff.spin_off_chance(make_parent(staff=10.0)[1], "mill", world)
many = spinoff.spin_off_chance(make_parent(staff=100.0)[1], "mill", world)
check("more staff, more chance", many > few > 0.0, (few, many))
young = make_parent()[1]
young.record.opened_year["mill"] = 99
check("a concern too young spawns nothing", spinoff.spin_off_chance(young, "mill", world) == 0.0)
check("the chance is capped", spinoff.spin_off_chance(make_parent(staff=1e9)[1], "mill", world) <= spinoff.SPINOFF_CHANCE_CAP)

# ---- founding ------------------------------------------------------------------------------------------
original_cap, original_rate = spinoff.SPINOFF_CHANCE_CAP, spinoff.SPINOFF_CHANCE_PER_STAFF_YEAR
spinoff.SPINOFF_CHANCE_CAP = 1.0
spinoff.SPINOFF_CHANCE_PER_STAFF_YEAR = 1.0
founded = spinoff.consider_spinoffs(registry, world)
check("a rival is founded", len(founded) == 1, founded)
rival = registry.get(founded[0])
check("it runs a copy of the concern", rival.kind == "firm" and "mill" in rival.concerns and rival.record.spun_off_from == "firm:1")
check("it learned the know-how, and the parent kept its own", {"gear", "mill"} <= rival.knowledge and {"gear", "mill"} <= parent.knowledge)
check("the parent still runs its concern", "mill" in parent.concerns)
check("the stake is pooled capital, booked as an edge", rival.money > 0.0 and any(key.startswith("edge:") for key in rival.record.income), rival.record.income)
check("the parent's money is untouched", parent.money == 1000.0)
check("one rival a parent a year", len(spinoff.consider_spinoffs(registry, world)) <= 1)

# ---- a player's staff leave too -------------------------------------------------------------------------
registry, owner = make_parent("player")
check("a player's concern can spawn a rival", len(spinoff.consider_spinoffs(registry, world)) == 1)

# ---- what stops it ---------------------------------------------------------------------------------------
registry, parent = make_parent()
world.patent = {"holder": "player:z", "expires": 200, "licensees": []}
check("a patent on the concern stops a rival", spinoff.consider_spinoffs(registry, world) == [])
world.patent = None
world.output = 1.0
check("capital too thin to fund the stake stops it", spinoff.consider_spinoffs(registry, world) == [])
world.output = 1.0e9
world.nodes["mill"]["rev"] = 0.0
check("a concern that would not pay an entrant spawns none", spinoff.consider_spinoffs(registry, world) == [])
world.nodes["mill"]["rev"] = 2000.0
spinoff.SPINOFF_CHANCE_CAP = 0.0
check("no chance, no rival", spinoff.consider_spinoffs(registry, world) == [])
spinoff.SPINOFF_CHANCE_CAP = original_cap
spinoff.SPINOFF_CHANCE_PER_STAFF_YEAR = original_rate
