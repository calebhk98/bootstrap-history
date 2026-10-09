"""Complaint 103: a patent is a right the state backs only as far as its reach. Practising a patented concern
unlicensed is a risk that follows how well the state enforces, not a block: entry and spin-off go ahead, the
expected damages come off what an entrant expects, and a holder who catches an infringer is paid its margin."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import enforcement, exchange_commands, patent, spinoff  # noqa: F401

from .agents_fake_world import FakeWorld, make_node, total_money


class EnforcedWorld(FakeWorld):
	capacity = 1.0
	registry = None

	def state_capacity(self):
		return self.capacity

	def patent_entry(self, node_id):
		return patent.entry_among(self.registry.actors.values(), node_id, self.year)

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id].get("rev", 0.0)) / (1.0 + rivals + entrants)

	def proof_years(self, node_id):
		return 0.0


def make_world(capacity):
	world = EnforcedWorld(year=100)
	world.capacity = capacity
	world.baseline = {"base"}
	world.nodes["base"] = make_node("base")
	world.nodes["mill"] = make_node("mill", ["base"], hours=100.0, revenue=2000.0)
	world.registry = ActorRegistry(ActorsState(home_country="home"))
	return world


def setup(capacity):
	world = make_world(capacity)
	registry = world.registry
	holder = registry.add("firm:1", ActorRecord(kind="firm", money=1000.0, founded_year=50))
	holder.knowledge.add("mill")
	holder.record.patents["mill"] = {"granted": 90, "expires": 110, "licensees": []}
	infringer = registry.add("firm:2", ActorRecord(kind="firm", money=1000.0, founded_year=60, last_margin=500.0))
	infringer.knowledge.add("mill")
	infringer.concerns.add("mill")
	licensed = registry.add("firm:3", ActorRecord(kind="firm", money=1000.0, founded_year=60, last_margin=500.0))
	licensed.knowledge.add("mill")
	licensed.concerns.add("mill")
	holder.record.patents["mill"]["licensees"].append("firm:3")
	return world, registry, holder, infringer, licensed


# ---- a state that reaches everywhere catches every unlicensed operator ------------------------------
world, registry, holder, infringer, licensed = setup(1.0)
before = total_money(registry.actors.values())
paid = enforcement.enforce_patents(registry, world)
check("a caught infringer pays the holder its margin", holder.money == 1500.0 and infringer.money == 500.0, (holder.money, infringer.money))
check("a licensee is left alone", licensed.money == 1000.0)
check("the holder never sues itself", holder.record.income.get("damages", 0.0) == 500.0)
check("damages move through the ledger and conserve money", abs(total_money(registry.actors.values()) - before) < 1e-9)
check("the spawner is registered", "patent_enforcement" in dict(__import__("sim.agents.registry", fromlist=["SPAWNERS"]).SPAWNERS))

# ---- a state with no reach catches nobody ------------------------------------------------------------
world, registry, holder, infringer, licensed = setup(0.0)
enforcement.enforce_patents(registry, world)
check("a state with no capacity enforces nothing", infringer.money == 1000.0 and holder.money == 1000.0)

# ---- the damages never exceed the infringer's purse --------------------------------------------------
world, registry, holder, infringer, licensed = setup(1.0)
infringer.record.money = 100.0
enforcement.enforce_patents(registry, world)
check("an infringer pays no more than it holds", infringer.money == 0.0 and holder.money == 1100.0, (infringer.money, holder.money))

# ---- expected damages come off what an entrant expects -----------------------------------------------
world, registry, holder, infringer, licensed = setup(0.4)
newcomer = registry.add("firm:9", ActorRecord(kind="firm", money=10.0))
check("an unlicensed entrant weighs the state's reach times its margin", abs(enforcement.expected_damages(world, newcomer.actor_id, "mill", 1000.0) - 400.0) < 1e-9)
check("a licensee expects none", enforcement.expected_damages(world, licensed.actor_id, "mill", 1000.0) == 0.0)
check("the holder expects none", enforcement.expected_damages(world, holder.actor_id, "mill", 1000.0) == 0.0)
check("nothing patented, nothing expected", enforcement.expected_damages(world, newcomer.actor_id, "base", 1000.0) == 0.0)

# ---- a spin-off is no longer blocked by a patent -----------------------------------------------------
world, registry, holder, infringer, licensed = setup(0.0)
world.output = 1.0e9
parent = registry.add("firm:7", ActorRecord(kind="firm", money=1000.0, founded_year=50))
parent.knowledge.update({"mill"})
parent.concerns.add("mill")
parent.record.opened_year["mill"] = 80
parent.workforce["labourer"] = 500.0
original = spinoff.SPINOFF_CHANCE_PER_STAFF_YEAR
spinoff.SPINOFF_CHANCE_PER_STAFF_YEAR = 1.0
founded = spinoff.consider_spinoffs(registry, world)
spinoff.SPINOFF_CHANCE_PER_STAFF_YEAR = original
check("a rival is founded on a patented concern where the state cannot enforce", len(founded) >= 1, founded)


# ---- the founder is an actor like any other: a seat running a patented concern unlicensed is pursued too ----
class SeatParty:
	kind = "household"
	actor_id = "founder"

	def __init__(self):
		self.record = ActorRecord(kind="household")
		self.concerns = {"mill"}
		self.money = 900.0

	def debit(self, amount, purpose):
		self.money -= amount

	def credit(self, amount, purpose):
		self.money += amount


class SeatWorld(EnforcedWorld):
	def seat_parties(self):
		return {"founder": self.seat}

	def seat_margin(self, seat_id):
		return 300.0


world, registry, holder, infringer, licensed = setup(1.0)
seat_world = SeatWorld(year=100)
seat_world.capacity, seat_world.registry, seat_world.nodes = 1.0, registry, world.nodes
seat_world.seat = SeatParty()
enforcement.enforce_patents(registry, seat_world)
check("the founder pays the holder its margin on the concern", seat_world.seat.money == 600.0 and holder.money == 1800.0, (seat_world.seat.money, holder.money))
holder.record.patents["mill"]["licensees"].append("founder")
seat_world.seat.money = 900.0
enforcement.enforce_patents(registry, seat_world)
check("a licensed founder is left alone", seat_world.seat.money == 900.0)
