"""Patents and company shares: a state that knows the institution grants an exclusive right, the right
and equity change hands through exchange, licences let others practise, and dividends go by share."""
from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import exchange, exchange_commands, joint_stock, licence, patent, player  # noqa: F401
from sim.agents import registry as registry_module
from sim.agents.player_commands import CommandRejected, run_orders

from .agents_fake_world import FakeWorld, make_node, total_money


class PatentWorld(FakeWorld):
	institution = True
	registry = None

	def state_grants_patents(self, actor):
		return self.institution

	def patent_entry(self, node_id):
		return patent.entry_among(self.registry.actors.values(), node_id, self.year)

	def proof_years(self, node_id):
		return 0.0


def raises(call):
	try:
		call()
	except CommandRejected as reason:
		return str(reason)
	return None


def make_world():
	world = PatentWorld()
	world.baseline = {"base"}
	world.nodes["base"] = make_node("base")
	world.nodes["loom"] = make_node("loom", ["base"])
	world.nodes["pump"] = make_node("pump", ["base"])
	world.registry = ActorRegistry(ActorsState(home_country="home"))
	return world


world = make_world()
registry = world.registry
a = registry.add("player:a", ActorRecord(kind="player", money=1000.0, controller="human"))
b = registry.add("player:b", ActorRecord(kind="player", money=1000.0, controller="human"))
c = registry.add("player:c", ActorRecord(kind="player", money=1000.0, controller="human"))
a.knowledge.add("loom")

# ---- granting ------------------------------------------------------------------------------
world.institution = False
check("no state that knows the institution, no patent", raises(lambda: patent.apply(a, "loom", world)))
world.institution = True
check("an actor must know what it patents", raises(lambda: patent.apply(b, "loom", world)))
check("a baseline technique cannot be patented", raises(lambda: patent.apply(a, "base", world)))
patent.apply(a, "loom", world)
entry = dict(a.record.patents["loom"])
check("the grant records the term", entry["expires"] > world.year and entry["granted"] == world.year, entry)
check("a second claim is refused while the right lives", raises(lambda: patent.apply(a, "loom", world)))
check("the holder is found", patent.holder_of(world, "loom") == "player:a")
b.knowledge.add("loom")
check("someone else is blocked from practising it", patent.blocked_reason(world, b, "loom") != "")
check("the holder is not", patent.blocked_reason(world, a, "loom") == "")

# ---- exchange: sell the right ---------------------------------------------------------------
before = total_money([a, b, c])
check("a right not held cannot be offered", raises(lambda: exchange.make_offer(b, c, {"patent": ["loom"]}, {}, world)))
offer = exchange.make_offer(a, b, {"patent": ["loom"]}, {"money": 300.0}, world)
exchange.accept(b, offer["id"], registry.get, world)
check("the right moves with its term", "loom" not in a.record.patents and b.record.patents["loom"]["expires"] == entry["expires"])
check("it was paid for through the ledger", a.money == 1300.0 and b.money == 700.0 and abs(total_money([a, b, c]) - before) < 1e-9)
check("the buyer now holds it", patent.holder_of(world, "loom") == "player:b" and patent.blocked_reason(world, a, "loom") != "")
check("an actor cannot offer a right it lost", raises(lambda: exchange.make_offer(a, c, {"patent": ["loom"]}, {}, world)))

# ---- exchange: licence the right -------------------------------------------------------------
c.knowledge.add("loom")
offer = exchange.make_offer(b, c, {"licence": ["loom"]}, {"money": 50.0}, world)
exchange.accept(c, offer["id"], registry.get, world)
check("a licensee may practise", patent.blocked_reason(world, c, "loom") == "" and "player:c" in b.record.patents["loom"]["licensees"])
check("the holder keeps the right", patent.holder_of(world, "loom") == "player:b")
check("only the holder can licence", raises(lambda: exchange.make_offer(a, c, {"licence": ["loom"]}, {}, world)))
b.concerns.add("loom")
offer = exchange.make_offer(b, a, {"concern": "loom"}, {}, world)
check("a concern cannot move to someone who needs a licence",
	  "licence" in (raises(lambda: exchange.accept(a, offer["id"], registry.get, world)) or "") and "loom" in b.concerns)
world.year = entry["expires"] + 1
check("a right lapses at the end of its term", patent.holder_of(world, "loom") is None and patent.blocked_reason(world, a, "loom") == "")
world.year = 100

# ---- the licence function respects a patent ---------------------------------------------------
d = registry.add("player:d", ActorRecord(kind="player", money=100.0, controller="human"))
world.demonstrated_nodes = {"loom"}
b.record.patents["loom"] = {"granted": 100, "expires": 110, "licensees": []}
check("a licence from someone who does not hold the patent is refused", licence.grant(a, d, "loom", 10.0, world) is False)

# ---- company shares -----------------------------------------------------------------------------
world = make_world()
registry = world.registry
firm = registry.add("firm:1", ActorRecord(kind="firm", money=500.0, last_margin=100.0, founded_year=90))
founder = registry.add("player:f", ActorRecord(kind="player", money=1000.0, controller="human"))
rich = registry.add("player:r", ActorRecord(kind="player", money=1000.0, controller="ai"))
check("a firm starts with no outside shareholders", firm.record.issued == 0.0)
check("one cannot sell more than one holds", raises(lambda: exchange.make_offer(founder, rich, {"shares": {"firm:1": 0.2}}, {}, world)))
check("it cannot issue more than it owns", raises(lambda: exchange.make_offer(firm, rich, {"shares": {"firm:1": 1.5}}, {}, world)))
offer = exchange.make_offer(firm, rich, {"shares": {"firm:1": 0.3}}, {"money": 200.0}, world)
exchange.accept(rich, offer["id"], registry.get, world)
check("an issue moves money to the firm and shares to the buyer",
	  firm.money == 700.0 and rich.money == 800.0 and abs(rich.record.holdings["firm:1"] - 0.3) < 1e-9
	  and abs(firm.record.issued - 0.3) < 1e-9, (firm.money, rich.money, rich.record.holdings, firm.record.issued))
check("issuing more than remains is refused", raises(lambda: exchange.make_offer(firm, rich, {"shares": {"firm:1": 0.8}}, {}, world)))
offer = exchange.make_offer(rich, founder, {"shares": {"firm:1": 0.1}}, {"money": 60.0}, world)
exchange.accept(founder, offer["id"], registry.get, world)
check("shares trade between holders", abs(rich.record.holdings["firm:1"] - 0.2) < 1e-9 and abs(founder.record.holdings["firm:1"] - 0.1) < 1e-9)
check("trading does not change what the firm has issued", abs(firm.record.issued - 0.3) < 1e-9)
check("issued matches the holdings", abs(joint_stock.held_in(registry.actors.values(), "firm:1") - firm.record.issued) < 1e-9)

# ---- dividends --------------------------------------------------------------------------------
rich_before, founder_before = rich.money, founder.money
before = total_money(registry.actors.values())
paid = joint_stock.pay_dividends(registry, world)
gain_rich, gain_founder = rich.money - rich_before, founder.money - founder_before
check("dividends are paid by share", paid > 0 and gain_rich > 0 and gain_founder > 0, (gain_rich, gain_founder, paid))
check("each holder gets in proportion to its share", abs(gain_rich / gain_founder - 2.0) < 1e-6, (gain_rich, gain_founder))
check("dividends conserve money", abs(total_money(registry.actors.values()) - before) < 1e-9)
check("a firm never pays beyond its purse", firm.money >= 0.0)
firm.money = 0.0
check("a firm with nothing pays nothing", joint_stock.pay_dividends(registry, world) == 0.0)
firm.record.last_margin = -50.0
firm.money = 500.0
check("a firm at a loss pays nothing", joint_stock.pay_dividends(registry, world) == 0.0)
check("the spawner is registered", "dividends" in dict(registry_module.SPAWNERS))

# ---- the AI values shares by what the firm earns ---------------------------------------------------
firm.record.last_margin = 100.0
founder.record.controller = "ai"
founder.money = 1000.0
founder.record.offers.clear()
rich.record.controller = "human"
exchange.make_offer(rich, founder, {"shares": {"firm:1": 0.1}}, {"money": 1.0}, world)
exchange.make_offer(rich, founder, {"shares": {"firm:1": 0.1}}, {"money": 900.0}, world)
exchange_commands.answer_offers(founder, registry.get, world)
check("an AI actor takes cheap shares and refuses dear ones",
	  abs(founder.record.holdings["firm:1"] - 0.2) < 1e-9 and founder.record.offers == [],
	  (founder.record.holdings, founder.record.offers))

# ---- the commands -----------------------------------------------------------------------------------
world = make_world()
registry = world.registry
a = registry.add("player:a", ActorRecord(kind="player", money=100.0, controller="human"))
a.knowledge.add("pump")
a.record.orders.append({"command": "patent", "node": "pump"})
run_orders(a, world)
check("the patent command is journalled and grants", a.record.journal[-1]["ok"] and "pump" in a.record.patents, a.record.journal)
a.record.orders.append({"command": "patent", "node": "pump"})
run_orders(a, world)
check("a repeat claim is journalled as failed", not a.record.journal[-1]["ok"])
