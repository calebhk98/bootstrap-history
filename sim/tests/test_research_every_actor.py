"""Complaint 491: one research path for every actor. A state, a firm and a player research a node through the
same function and pay the same; progress scales with the country's literacy; known nodes diffuse between actors."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, Firm
from sim.agents.government import Government
from sim.agents.player import Player
from sim.agents import research

from .agents_fake_world import FakeWorld, make_node


class ResearchWorld(FakeWorld):
	def __init__(self, productivity=1.0, half_life=0.001):
		super().__init__()
		self.productivity = productivity
		self.half_life = half_life
		self.baseline = {"base"}
		self.nodes["base"] = make_node("base")
		self.nodes["tech"] = make_node("tech", ["base"], hours=100.0, years=2.0)
		self.nodes["deep"] = make_node("deep", ["tech"], years=1.0)

	def research_productivity(self, country=None):
		return self.productivity

	def knowledge_half_life_years(self):
		return self.half_life

	def distance_km(self, place_a, place_b):
		return 0.0

	def knowledge_visibility(self, node_id, distance_km):
		return 1.0


def actors(money=5000.0):
	return {"state": Government("government:home", ActorRecord(kind="government", money=money)),
			"firm": Firm("firm:1", ActorRecord(kind="firm", money=money, founded_year=100)),
			"player": Player("player:2", ActorRecord(kind="player", money=money, founded_year=100))}


def years_to_learn(actor, world, node_id):
	actor.start_research(node_id, world)
	for year in range(1, 20):
		actor.work_on_research(world)
		world.year += 1
		if node_id in actor.knowledge:
			return year
	return None


# ---- the same function, the same price ----------------------------------------------------
paid = {}
for name, actor in actors().items():
	world = ResearchWorld()
	check("%s researches a node through the shared path" % name, years_to_learn(actor, world, "tech") == 2, name)
	paid[name] = 5000.0 - actor.money
check("a state, a firm and a player pay the same for the same node",
	  len({round(amount, 6) for amount in paid.values()}) == 1 and paid["state"] > 0, paid)
check("the plan is the same function for every actor",
	  len({round(research.plan(actor, "tech", ResearchWorld())["total"], 6) for actor in actors().values()}) == 1)

# ---- gates --------------------------------------------------------------------------------
for name, actor in actors().items():
	world = ResearchWorld()
	try:
		actor.start_research("deep", world)
		refused = False
	except Exception as reason:
		refused = "tech" in str(reason)
	check("%s cannot research past a prerequisite it lacks" % name, refused and not actor.works, name)
	poor = actors(money=1.0)[name]
	try:
		poor.start_research("tech", world)
		refused = False
	except Exception:
		refused = True
	check("%s cannot start research its purse cannot pay" % name, refused and not poor.works, name)

# ---- literacy scales progress -------------------------------------------------------------
slow = years_to_learn(actors()["firm"], ResearchWorld(productivity=0.5), "tech")
fast = years_to_learn(actors()["firm"], ResearchWorld(productivity=1.0), "tech")
check("a less literate country researches more slowly", slow is not None and fast is not None and slow > fast, (slow, fast))

# ---- research and copying do not mistake each other's work --------------------------------
firm = actors()["firm"]
world = ResearchWorld()
firm.start_research("tech", world)
check("a research project is not advanced as a copy", firm.work_on_copies(world) == [] and firm.works["tech"]["progress"] == 0.0)

# ---- diffusion between actors --------------------------------------------------------------
world = ResearchWorld()
group = actors()
group["firm"].knowledge.add("tech")
research.diffuse(list(group.values()), world)
check("a node one actor knows reaches the others", "tech" in group["state"].knowledge and "tech" in group["player"].knowledge)

world = ResearchWorld()
group = actors()
group["firm"].knowledge.add("deep")
research.diffuse(list(group.values()), world)
check("a node diffuses only to an actor that knows what it rests on", "deep" not in group["state"].knowledge)

world = ResearchWorld(half_life=1e9)
group = actors()
group["firm"].knowledge.add("tech")
research.diffuse(list(group.values()), world)
check("with a very slow half-life nothing spreads in a year", "tech" not in group["state"].knowledge)
