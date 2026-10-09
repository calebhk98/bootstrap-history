"""A player is an actor of its own: it researches any node whose prerequisites it knows, runs concerns,
obeys queued commands and journals each, and shares one concern rule with the firm."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, Firm, ledger
from sim.agents import firm_entry, registry as registry_module
from sim.agents.player import Player
from sim.agents.player_commands import register_command
from sim.agents.tuning_player import PLAYER_JOURNAL_LIMIT

from .agents_fake_world import FakeWorld, make_node, total_money


class PlayerWorld(FakeWorld):
	"""The fake world plus what a player's decisions ask of a real one."""

	def __init__(self, seed: int = 1) -> None:
		super().__init__(seed=seed)
		self.exposures = {}

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id].get("rev", 0.0)) / (rivals + entrants)

	def proof_years(self, node_id):
		return 0.0

	def exposure(self, node_id, location):
		return self.exposures.get(node_id, 1.0)


def make_world(seed=1, risk=0.0):
	world = PlayerWorld(seed)
	world.baseline = {"base", "shop"}
	world.nodes["base"] = make_node("base")
	world.nodes["tech"] = make_node("tech", ["base"], hours=100.0, years=3.0, revenue=0.0)
	world.nodes["tech"]["risk"] = risk
	world.nodes["deep"] = make_node("deep", ["tech"], years=1.0)
	world.nodes["shop"] = make_node("shop", ["base"], hours=100.0, years=1.0, revenue=500.0, upkeep=50.0)
	world.nodes["mill"] = make_node("mill", ["base"], hours=100.0, years=2.0, revenue=2000.0, upkeep=100.0)
	return world


def make_player(actor_id="player:2", money=1000.0, controller="human", world=None):
	player = Player(actor_id, ActorRecord(kind="player", money=money, controller=controller, founded_year=100))
	return player


def year_on(player, world):
	player.advance(world)
	world.year += 1


def last_entry(player):
	return player.record.journal[-1]


# ---- research -----------------------------------------------------------------------------
world = make_world()
player = make_player()
player.record.orders.append({"command": "research", "node": "tech"})
year_on(player, world)
check("research is not done before the node's years", "tech" not in player.knowledge and "tech" in player.works)
year_on(player, world)
check("research is still going in its second year", "tech" not in player.knowledge)
year_on(player, world)
check("research completes over the node's years and adds to knowledge",
	  "tech" in player.knowledge and "tech" not in player.works, player.knowledge)
check("the orders are cleared once run", player.record.orders == [])
check("the journal says the research began", player.record.journal[0]["ok"] and player.record.journal[0]["command"] == "research")
paid = sum(player.record.outlays.values())
check("research is paid from the purse", abs(1000.0 - player.money - paid) < 1e-6 and paid > 0, (player.money, paid))
check("money is the opening purse plus income less outlays",
	  abs(player.money - (1000.0 + sum(player.record.income.values()) - sum(player.record.outlays.values()))) < 1e-6)
check("a researched node's dependants become researchable", player.knows("tech", world) and not player.knows("deep", world))

world = make_world()
player = make_player()
player.record.orders.append({"command": "research", "node": "deep"})
year_on(player, world)
check("a node whose prerequisites are unknown is rejected with the reason",
	  not last_entry(player)["ok"] and "tech" in last_entry(player)["detail"], last_entry(player))
check("a rejected research starts no work and costs nothing", not player.works and player.money == 1000.0)

poor = make_player(money=10.0)
poor.record.orders.append({"command": "research", "node": "tech"})
year_on(poor, world)
check("research the purse cannot pay for is rejected", not last_entry(poor)["ok"] and not poor.works, last_entry(poor))

failed_world = make_world(risk=1.0)
player = make_player()
player.record.orders.append({"command": "research", "node": "tech"})
for _year in range(4):
	year_on(player, failed_world)
check("research can fail, and the money is gone", "tech" not in player.knowledge and not player.works and player.money < 1000.0)
check("a failure is counted", player.record.failed_copies.get("tech") == 1, player.record.failed_copies)

# ---- opening and closing a concern ---------------------------------------------------------
world = make_world()
player = make_player()
player.record.orders.append({"command": "open", "node": "shop"})
year_on(player, world)
check("open runs a concern and yields takings less upkeep and wages",
	  "shop" in player.concerns and abs(player.money - (1000.0 + 500.0 - 50.0 - 100.0)) < 1e-6, player.money)
check("the concern's margin is on the record", abs(player.record.margins["shop"] - 350.0) < 1e-6, player.record.margins)
player.record.orders.append({"command": "close", "node": "shop"})
before = player.money
year_on(player, world)
check("close stops the concern", "shop" not in player.concerns and abs(player.money - before) < 1e-6, player.money)
check("close forgets the concern's margin", "shop" not in player.record.margins)

player = make_player()
player.record.orders.append({"command": "open", "node": "deep"})
player.record.orders.append({"command": "close", "node": "shop"})
year_on(player, world)
check("opening what the player cannot make is rejected", not player.record.journal[0]["ok"], player.record.journal[0])
check("closing what is not open is rejected", not player.record.journal[1]["ok"], player.record.journal[1])

# ---- transfer ------------------------------------------------------------------------------
world = make_world()
payer, payee = make_player("player:2", 1000.0), make_player("player:3", 50.0)
found = {"player:2": payer, "player:3": payee}
Player.find_actor = found.get
try:
	payer.record.orders.append({"command": "transfer", "to": "player:3", "amount": 300.0})
	before_sum = total_money([payer, payee])
	year_on(payer, world)
	check("transfer moves money between two players", payer.money == 700.0 and payee.money == 350.0, (payer.money, payee.money))
	check("the sum of the purses is unchanged", total_money([payer, payee]) == before_sum)
	payer.record.orders.append({"command": "transfer", "to": "player:9", "amount": 1.0})
	payer.record.orders.append({"command": "transfer", "to": "player:3", "amount": 5000.0})
	payer.record.orders.append({"command": "transfer", "to": "player:3", "amount": -5.0})
	payer.record.orders.append({"command": "transfer", "to": "player:3", "amount": "lots"})
	year_on(payer, world)
	check("transfers to nobody, beyond the purse, negative or malformed are all rejected",
		  [entry["ok"] for entry in payer.record.journal[-4:]] == [False] * 4 and total_money([payer, payee]) == before_sum,
		  payer.record.journal[-4:])
finally:
	del Player.find_actor
	Player.find_actor = None

# ---- bad commands and the journal ----------------------------------------------------------
world = make_world()
player = make_player()
player.record.orders.extend([{"command": "levitate"}, "research", {"node": "tech"}, {"command": "research"}])
year_on(player, world)
check("unknown, malformed and incomplete commands are rejected, never raised",
	  [entry["ok"] for entry in player.record.journal] == [False] * 4, player.record.journal)
check("an unknown command's reason is given", player.record.journal[0]["detail"] == "unknown command")

player = make_player()
for index in range(PLAYER_JOURNAL_LIMIT + 20):
	player.record.orders.append({"command": "bad%d" % index})
year_on(player, world)
check("the journal keeps only the most recent entries",
	  len(player.record.journal) == PLAYER_JOURNAL_LIMIT
	  and player.record.journal[-1]["command"] == "bad%d" % (PLAYER_JOURNAL_LIMIT + 19))

register_command("shout", lambda actor, order, seen: "heard " + order["word"])
player = make_player()
player.record.orders.append({"command": "shout", "word": "hello"})
year_on(player, world)
check("a registered command runs", last_entry(player)["ok"] and last_entry(player)["detail"] == "heard hello", last_entry(player))

# ---- who drives the player -----------------------------------------------------------------
world = make_world()
human = make_player(controller="human")
for _year in range(5):
	year_on(human, world)
check("a human player with no orders does nothing",
	  human.money == 1000.0 and not human.works and not human.concerns and not human.knowledge and not human.record.journal)

world = make_world()
world.nodes["dud"] = make_node("dud", ["base"], revenue=0.0)
robot = make_player(money=5000.0, controller="ai")
for _year in range(6):
	year_on(robot, world)
check("an AI player researches and opens something profitable within a few years",
	  "tech" not in robot.works and "mill" in robot.concerns and robot.money > 5000.0, (robot.concerns, robot.money, robot.knowledge))
check("an AI player does not research what could never pay", "dud" not in robot.knowledge and "dud" not in robot.works)

# ---- what competitors may enter after ------------------------------------------------------
world = make_world()
operator = make_player()
operator.record.orders.append({"command": "open", "node": "shop"})
year_on(operator, world)
world.public_nodes.add("shop")
check("a profitable concern in public view is proven", operator.proven_concerns(world) == ["shop"], operator.proven_concerns(world))
world.public_nodes.clear()
world.exposures["shop"] = 0.0
check("a profitable concern nobody can see is not", operator.proven_concerns(world) == [])
world.exposures["shop"] = 1.0
operator.record.margins["shop"] = -1.0
check("a concern running at a loss is not", operator.proven_concerns(world) == [])

# ---- the firm runs through the same rule ----------------------------------------------------
world = make_world()
firm = Firm("firm:1", ActorRecord(kind="firm", money=1000.0, founded_year=90))
firm.concerns.add("shop")
firm.record.opened_year["shop"] = 95
firm.rivals_of = lambda node_id, asking_id: 1.0
firm.operate(world)
managing = firm_entry.management_cost(world, "shop")
check("a firm's year through the shared rule: takings less upkeep, wages and management",
	  managing > 0.0 and abs(firm.money - (1000.0 + 250.0 - 50.0 - 100.0 - managing)) < 1e-6
	  and abs(firm.record.last_margin - (100.0 - managing)) < 1e-6, firm.money)
check("a firm's staffing and loss years are kept", firm.record.staffing["shop"] == 1.0 and firm.record.loss_years == 0)
world.free_people["labourer"] = 0.0
firm.operate(world)
check("a firm that finds no staff makes nothing and loses its upkeep",
	  firm.record.staffing["shop"] == 0.0 and firm.record.loss_years == 1 and abs(firm.record.last_margin + 50.0 + managing) < 1e-6, firm.record.last_margin)

# ---- deterministic with the same seed -------------------------------------------------------
def run(seed):
	world = make_world(seed=seed, risk=0.5)
	robot = make_player(money=5000.0, controller="ai")
	for _year in range(8):
		year_on(robot, world)
	return sorted(robot.knowledge), sorted(robot.concerns), robot.money, robot.record.journal


check("the same seed gives the same player history", run(3) == run(3))
check("the player kind is registered", registry_module.ACTOR_CLASSES.get("player") is Player)
