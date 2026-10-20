"""Complaint 491: every actor passes the founder's start gates before it researches: scholars, craftsmen, the
`req_any` substitutes and materials someone sells. One gate function serves the seat and the actors."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import research, research_gate
from sim.agents.player_commands import CommandRejected

from .test_research_every_actor import ResearchWorld, actors


def refused_cause(actor, world, node_id):
	try:
		research.begin(actor, node_id, world)
	except CommandRejected as reason:
		return reason.args[0].cause
	return None


def world_with(**node_fields):
	world = ResearchWorld()
	world.nodes["tech"].update(node_fields)
	return world


for name in actors():
	check("%s is refused a node needing scholars it cannot field" % name,
		  refused_cause(actors()[name], world_with(sch=2), "tech") == "scholar_staff", name)
	world = world_with(sch=2)
	world.hands["scholar"] = 2.0
	check("%s starts it once the scholars can be had" % name, refused_cause(actors()[name], world, "tech") is None, name)
	world = world_with(art=3)
	world.hands["craft"] = 2.0
	check("%s is refused with too few craftsmen" % name, refused_cause(actors()[name], world, "tech") == "craft_staff", name)
	world = world_with()
	world.unsold["tech"] = ["rubber"]
	check("%s is refused a material no one sells" % name, refused_cause(actors()[name], world, "tech") == "materials_unsold", name)

# ---- req_any substitutes -------------------------------------------------------------------
group = {"options": {"bronze_boiler": 0.6, "steel_boiler": 1.0, "coal_kg": 0.8}}
node = {"req_any": [group], "mat": {}}
is_technique = lambda option: option.endswith("boiler")
check("a technique the researcher lacks does not serve a substitute group",
	  research_gate.substitute_quality(node, {"options": {"bronze_boiler": 0.6}}, lambda option: False, is_technique, 0.9) == 0.0)
check("the best technique known serves at its stated quality",
	  research_gate.substitute_quality(node, group, lambda option: option == "steel_boiler", is_technique, 0.9) == 1.0)
check("a plain commodity serves at the discount",
	  abs(research_gate.substitute_quality(node, group, lambda option: False, is_technique, 0.9) - 0.72) < 1e-9)

for name in actors():
	actor = actors()[name]
	world = world_with(req_any=[{"options": {"bronze_boiler": 0.6}}])
	world.nodes["bronze_boiler"] = world.nodes["base"]
	check("%s is refused when no option of a req_any group is known" % name, refused_cause(actor, world, "tech") == "no_substitute", name)
	actor.knowledge.add("bronze_boiler")
	check("%s starts once it knows an option" % name, refused_cause(actor, world, "tech") is None, name)

check("the shortfall is the people missing, never negative",
	  research_gate.hands_short(3, 1.0) == 2.0 and research_gate.hands_short(1, 5.0) == 0.0)
