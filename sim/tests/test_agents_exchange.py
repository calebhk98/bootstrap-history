"""Actors trade with each other: money, stores, know-how and concerns change hands atomically through
the ledger, an AI actor answers offers by worth, and the commands write the journal."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import exchange, exchange_commands, player  # noqa: F401  (player registers its kind)
from sim.agents import registry as registry_module
from sim.agents.player_commands import CommandRejected, run_orders

from .agents_fake_world import FakeWorld, make_node, total_money


class ExchangeWorld(FakeWorld):
	def material_price(self, material):
		return self.prices.get(material, 0.0)

	def proof_years(self, node_id):
		return 0.0


def make_world():
	world = ExchangeWorld()
	world.baseline = {"base"}
	world.nodes["base"] = make_node("base")
	world.nodes["mill"] = make_node("mill", ["base"])
	world.nodes["forge"] = make_node("forge", ["base"])
	world.prices = {"grain": 10.0, "iron": 50.0}
	return world


def make_registry(**money):
	registry = ActorRegistry(ActorsState(home_country="home"))
	for name, purse in money.items():
		registry.add("player:" + name, ActorRecord(kind="player", money=purse, controller="human"))
	return registry


def raises(call):
	try:
		call()
	except CommandRejected as reason:
		return str(reason)
	return None


world = make_world()
registry = make_registry(a=1000.0, b=500.0)
a, b = registry.get("player:a"), registry.get("player:b")
everyone = [a, b]
a.record.stores["grain"] = 100.0
b.record.stores["iron"] = 10.0
before = total_money(everyone)

# ---- money for stores ---------------------------------------------------------------------
offer = exchange.make_offer(a, b, {"stores": {"grain": 40.0}}, {"money": 300.0}, world)
check("an offer waits in the receiver's record", b.record.offers == [offer] and not a.record.offers)
check("the offer is plain data", {"id", "from", "to", "give", "take", "year", "expires"} <= set(offer))
exchange.accept(b, offer["id"], registry.get, world)
check("accepting moves the stores exactly", a.record.stores["grain"] == 60.0 and b.record.stores["grain"] == 40.0)
check("accepting moves the money exactly", a.money == 1300.0 and b.money == 200.0, (a.money, b.money))
check("the offer is used up", b.record.offers == [])
check("total money is unchanged by a deal", abs(total_money(everyone) - before) < 1e-9)

# ---- an offer needs the giver to hold what it gives ---------------------------------------
check("an offer of what the giver lacks is refused", raises(lambda: exchange.make_offer(a, b, {"money": 1e9}, {}, world)))
check("an offer of stores it lacks is refused", raises(lambda: exchange.make_offer(a, b, {"stores": {"iron": 1.0}}, {}, world)))
check("an empty offer is refused", raises(lambda: exchange.make_offer(a, b, {}, {}, world)))
check("an offer to oneself is refused", raises(lambda: exchange.make_offer(a, a, {"money": 1.0}, {}, world)))
check("a negative amount is refused", raises(lambda: exchange.make_offer(a, b, {"money": -5.0}, {}, world)))

# ---- knowledge: the receiver learns, the giver keeps --------------------------------------
a.knowledge.add("mill")
offer = exchange.make_offer(a, b, {"knowledge": ["mill"]}, {"money": 100.0}, world)
exchange.accept(b, offer["id"], registry.get, world)
check("the receiver learns the node", "mill" in b.knowledge)
check("the giver keeps it", "mill" in a.knowledge)
check("it is paid for", a.money == 1400.0 and b.money == 100.0, (a.money, b.money))
check("a node the giver does not know cannot be offered",
	  raises(lambda: exchange.make_offer(a, b, {"knowledge": ["forge"]}, {}, world)))

# ---- a concern moves with its opened year and size ----------------------------------------
a.concerns.add("forge")
a.knowledge.add("forge")
a.record.opened_year["forge"] = 60
a.record.capacity["forge"] = 2.5
a.record.margins["forge"] = 12.0
offer = exchange.make_offer(a, b, {"concern": "forge"}, {"money": 50.0}, world)
check("a buyer who cannot know the concern is refused",
	  "cannot make forge" in (raises(lambda: exchange.accept(b, offer["id"], registry.get, world)) or "")
	  and "forge" in a.concerns and b.money == 100.0)
b.record.offers.clear()
offer = exchange.make_offer(a, b, {"concern": "forge", "knowledge": ["forge"]}, {"money": 50.0}, world)
exchange.accept(b, offer["id"], registry.get, world)
check("a concern arrives with the knowledge to run it", "forge" in b.concerns and "forge" not in a.concerns)
check("the concern keeps its opened year and size",
	  b.record.opened_year["forge"] == 60 and b.record.capacity["forge"] == 2.5
	  and "forge" not in a.record.opened_year and "forge" not in a.record.capacity)
check("the seller's margin record goes with it", "forge" not in a.record.margins)
a.knowledge.discard("forge")
b.concerns.discard("mill")
a.concerns.add("mill")
offer = exchange.make_offer(a, b, {"concern": "mill"}, {}, world)
exchange.accept(b, offer["id"], registry.get, world)
check("a buyer that already knows the node can take the concern", "mill" in b.concerns)

# ---- acceptance re-validates --------------------------------------------------------------
b.money, a.money = 1000.0, 1000.0
offer = exchange.make_offer(a, b, {"stores": {"grain": 10.0}}, {"money": 800.0}, world)
b.debit(900.0, "spent")
snapshot = (a.money, b.money, dict(a.record.stores), dict(b.record.stores))
reason = raises(lambda: exchange.accept(b, offer["id"], registry.get, world))
check("an offer the receiver can no longer pay is rejected", reason is not None, reason)
check("a rejected acceptance moves nothing",
	  snapshot == (a.money, b.money, dict(a.record.stores), dict(b.record.stores)))
b.credit(900.0, "found")
a.record.stores["grain"] = 0.0
reason = raises(lambda: exchange.accept(b, offer["id"], registry.get, world))
check("an offer the giver can no longer give is rejected, money unmoved", reason is not None and b.money == 1000.0, reason)
check("a payer never goes below zero", min(a.money, b.money) >= 0.0)

# ---- expiry and decline -------------------------------------------------------------------
b.record.offers.clear()
a.record.stores["grain"] = 50.0
offer = exchange.make_offer(a, b, {"stores": {"grain": 1.0}}, {}, world)
check("a live offer is kept", exchange.expire_offers(b, world.year) == [] and len(b.record.offers) == 1)
world.year = offer["expires"] + 1
check("an expired offer vanishes", exchange.expire_offers(b, world.year) == [offer["id"]] and b.record.offers == [])
world.year = 100
offer = exchange.make_offer(a, b, {"stores": {"grain": 1.0}}, {}, world)
exchange.decline(b, offer["id"])
check("a declined offer vanishes and nothing moves", b.record.offers == [] and a.record.stores["grain"] == 50.0)
check("an unknown offer is refused", raises(lambda: exchange.decline(b, "nope")))

# ---- the AI's answer ----------------------------------------------------------------------
world = make_world()
registry = ActorRegistry(ActorsState(home_country="home"))
human = registry.add("player:h", ActorRecord(kind="player", money=1000.0, controller="human"))
robot = registry.add("player:r", ActorRecord(kind="player", money=1000.0, controller="ai"))
human.record.stores["grain"] = 100.0
good = exchange.make_offer(human, robot, {"stores": {"grain": 50.0}}, {"money": 100.0}, world)
bad = exchange.make_offer(human, robot, {"stores": {"grain": 5.0}}, {"money": 400.0}, world)
before = total_money([human, robot])
dict(registry_module.SPAWNERS)["exchange_answers"](registry, world)
check("the spawner is registered", "exchange_answers" in dict(registry_module.SPAWNERS))
check("an AI actor accepts a good deal", robot.record.stores.get("grain") == 50.0 and robot.money == 900.0, (robot.money, robot.record.stores))
check("an AI actor declines a bad one", human.money == 1100.0 and robot.record.offers == [])
check("the AI's deals conserve money", abs(total_money([human, robot]) - before) < 1e-9)
human.record.controller = "human"
robot.record.controller = "human"
exchange.make_offer(human, robot, {"stores": {"grain": 50.0}}, {"money": 100.0}, world)
exchange_commands.answer_offers(robot, registry.get, world)
check("a human receiver is not answered for", len(robot.record.offers) == 1)

robot.record.controller = "ai"
robot.record.offers.clear()
robot.record.concerns.add("forge")
robot.record.margins["forge"] = 10.0
human.record.concerns.add("mill")
human.knowledge.update({"mill"})
robot.knowledge.add("mill")
exchange.make_offer(human, robot, {"concern": "mill"}, {"concern": "forge"}, world)
human.knowledge.add("forge")
exchange_commands.answer_offers(robot, registry.get, world)
check("an AI actor declines to give up a profitable concern for a worthless one",
	  "forge" in robot.concerns and "mill" in human.concerns)

# ---- the commands -------------------------------------------------------------------------
world = make_world()
registry = ActorRegistry(ActorsState(home_country="home"))
a = registry.add("player:a", ActorRecord(kind="player", money=1000.0, controller="human"))
b = registry.add("player:b", ActorRecord(kind="player", money=1000.0, controller="human"))
a.record.orders.append({"command": "offer", "to": "player:b", "give": {"money": 200.0}, "take": {}})
run_orders(a, world)
entry = a.record.journal[-1]
check("an offer command journals its result", entry["command"] == "offer" and entry["ok"], entry)
offer_id = b.record.offers[0]["id"]
b.record.orders.append({"command": "accept", "offer": offer_id})
run_orders(b, world)
check("an accept command does the deal and journals it",
	  b.record.journal[-1]["ok"] and a.money == 800.0 and b.money == 1200.0, b.record.journal)
a.record.orders.append({"command": "offer", "to": "player:b", "give": {"money": 5000.0}, "take": {}})
run_orders(a, world)
check("a refused offer is journalled as failed", not a.record.journal[-1]["ok"] and a.record.journal[-1]["detail"])
a.record.orders.append({"command": "offer", "to": "player:nobody", "give": {"money": 1.0}, "take": {}})
run_orders(a, world)
check("an offer to no one is journalled as failed", not a.record.journal[-1]["ok"])
a.record.orders.append({"command": "offer", "to": "player:b", "give": {"money": 10.0}, "take": {}})
run_orders(a, world)
b.record.orders.append({"command": "decline", "offer": b.record.offers[0]["id"]})
run_orders(b, world)
check("a decline command clears the offer", b.record.journal[-1]["ok"] and b.record.offers == [])
b.record.orders.append({"command": "accept", "offer": "missing"})
run_orders(b, world)
check("accepting an unknown offer is journalled as failed", not b.record.journal[-1]["ok"])
