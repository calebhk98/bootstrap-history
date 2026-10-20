"""Complaint 491: firms and states choose research themselves, through their decision policy. A firm takes a node
whose takings repay its cost over its horizon; a state takes nodes in the interests its priorities weight."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import research_choice
from sim.agents.policy import IdlePolicy

from .agents_fake_world import make_node
from .test_research_every_actor import ResearchWorld, actors


class ChoiceWorld(ResearchWorld):
	def __init__(self):
		super().__init__()
		self.nodes["pays"] = make_node("pays", ["base"], hours=100.0, years=1.0, revenue=100000.0)
		self.nodes["dear"] = make_node("dear", ["base"], hours=100.0, years=1.0, revenue=1.0)
		self.nodes["drill"] = make_node("drill", ["base"], hours=100.0, years=1.0)
		self.nodes["drill"]["gains"] = {"military": 1.0}
		self.nodes["drill"]["cost"] = 100.0
		self.nodes["pays"]["cost"] = 100.0
		self.nodes["dear"]["cost"] = 100000.0

	def entry_gross(self, node_id, rivals, capacity):
		return float(self.nodes[node_id].get("rev", 0.0))

	def state_weights(self):
		return {"military": 1.0}

	def state_revenue(self):
		return 5.0e8


group = actors()
world = ChoiceWorld()
begun = research_choice.decide(group["firm"], world)
check("a firm researches the node whose takings repay its cost", "pays" in begun and "pays" in group["firm"].works, begun)
check("...and not a node whose takings do not repay it", "dear" not in group["firm"].works and "drill" not in group["firm"].works)

begun = research_choice.decide(group["state"], world)
check("a state researches a node in the interests it weights", begun == ["drill"] and "drill" in group["state"].works, begun)
check("...and not a node that gains it nothing", "pays" not in group["state"].works)

idle = actors()["firm"]
idle.decision_policy = IdlePolicy()
check("the choice is the actor's policy's: an idle policy begins nothing", research_choice.decide(idle, ChoiceWorld()) == [] and not idle.works)

poor = actors(money=1.0)["firm"]
check("a firm that cannot pay for it begins nothing", research_choice.decide(poor, ChoiceWorld()) == [])

second = actors()["firm"]
research_choice.decide(second, ChoiceWorld())
check("a node under research is not begun twice", research_choice.decide(second, ChoiceWorld()) == [])
