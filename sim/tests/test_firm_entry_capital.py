"""Complaints 330/331/345/376: a firm is founded by a member of a stratum that holds savings, with a
fixed entry cost that rises with the operators crowding its market and a copy chance that depends on
the founder's literacy; a firm that earns less than its plant would lend for leaves and its purse
returns to its founder. Money between the founder and the firm is conserved."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import firm_entry, firm_exit
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld, make_node, total_money


class EntryWorld(FakeWorld):
	"""A world whose proven concern pays one entrant its takings shared among the sellers."""

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step


def make_world():
	world = EntryWorld()
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
	world.demonstrated_nodes = {"shop"}
	world.proven = {"shop"}
	return world


def make_registry(savings=None, literacy=0.5):
	registry = ActorRegistry(ActorsState(home_country="home"))
	if savings is not None:
		registry.add("stratum:home:merchants", ActorRecord(
			kind="stratum", stratum="merchants", members=100.0, money=savings, literacy=literacy))
	return registry


# ---- a founder's stake comes from a stratum's savings, and money is conserved
world = make_world()
registry = make_registry(savings=1.0e6)
before = total_money(registry.actors.values())
founded = registry.consider_entry(world)
firm = registry.actors[founded[0]] if founded else None
check("a stratum with savings founds a firm", firm is not None, founded)
if firm is not None:
	stratum = registry.actors["stratum:home:merchants"]
	paid = firm.record.income.get("founding stake", 0.0)
	check("the firm is funded from the stratum's purse", paid > 0.0 and stratum.money == 1.0e6 - paid, (paid, stratum.money))
	check("the firm names its founder", firm.record.plan.get("founder") == stratum.actor_id, firm.record.plan)
	premium = firm.record.outlays.get("edge:entry premium", 0.0)
	check("money is conserved but for the entry premium that leaves the modelled actors",
		abs(total_money(registry.actors.values()) - (before - premium)) < 1e-6,
		(before, total_money(registry.actors.values()), premium))

# ---- no savings, no founder
registry = make_registry(savings=0.0)
check("strata with no savings found no firm", registry.consider_entry(make_world()) == [])

# ---- no strata: the pooled capital rule stands, booked as an edge
registry = make_registry()
founded = registry.consider_entry(make_world())
check("a world without strata falls back to the pooled capital", len(founded) == 1, founded)
if founded:
	check("pooled capital is booked as an edge", registry.actors[founded[0]].record.income.get("edge:pooled capital", 0.0) > 0.0,
		registry.actors[founded[0]].record.income)

# ---- crowding raises what entry costs and bars entry in a crowded market
check("a crowded market costs an entrant more to enter",
	firm_entry.entry_premium(1000.0, 20) > firm_entry.entry_premium(1000.0, 2) > firm_entry.entry_premium(1000.0, 0) == 0.0)


def entrants_into(existing):
	registry = make_registry(savings=1.0e9)
	for number in range(existing):
		registry.add("firm:%d" % (number + 100), ActorRecord(kind="firm", concerns={"shop"}, founded_year=0))
	return len(registry.consider_entry(make_world()))


check("an empty market draws an entrant and a crowded one does not", entrants_into(0) == 1 and entrants_into(300) == 0,
	(entrants_into(0), entrants_into(300)))

# ---- literacy: an unlettered founder copies less surely
literate = Stratum("stratum:a", ActorRecord(kind="stratum", literacy=1.0))
unlettered = Stratum("stratum:b", ActorRecord(kind="stratum", literacy=0.0))
check("a lettered founder copies more surely than an unlettered one",
	firm_entry.copy_ease(literate) == 1.0 and firm_entry.copy_ease(unlettered) < firm_entry.copy_ease(literate))

# ---- a firm that earns less than its plant would lend for leaves, and gives its purse back
world = make_world()
world.year = 50
world.rate = 0.05
registry = make_registry(savings=0.0)
founder = registry.actors["stratum:home:merchants"]
weak = registry.add("firm:9", ActorRecord(kind="firm", money=500.0, founded_year=0, concerns={"shop"},
	opened_year={"shop": 0}, last_margin=10.0, plan={"founder": founder.actor_id}))
before = total_money(registry.actors.values())
check("a thin margin on a costly plant counts as weak", firm_exit.earns_less_than_plant_would_lend_for(weak, world))
weak.record.last_margin = 1.0e6
check("a margin above what the plant would earn lent out is not weak", not firm_exit.earns_less_than_plant_would_lend_for(weak, world))
firm_exit.close_firm(weak, world)
check("a closed firm hands its purse back to its founder", founder.money == 500.0 and weak.money == 0.0, (founder.money, weak.money))
check("closing a firm conserves money", abs(total_money(registry.actors.values()) - before) < 1e-9)
check("a closed firm runs nothing", weak.record.exited_year == 50 and not weak.concerns)
