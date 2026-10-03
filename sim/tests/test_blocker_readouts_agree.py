"""One classifier names every blocker: Complaints/125, 263 (and 234, 238, 239, 268 below)."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_screens_big import render_why

SUPPLY_NODE = "mat_bulk_steel"


def supply_sim():
	test_sim = sim(capital=1e9)
	test_sim.done.update(NODES[SUPPLY_NODE]["pre"])
	test_sim._done_changed()
	return test_sim


def kinds_of(test_sim, node_id):
	return [blocker["kind"] for blocker in test_sim.start_blockers(node_id)]


# --- one node per kind, the kind and the refusal text come from one place
check("missing prerequisites are a knowledge blocker",
      kinds_of(sim(capital=1e9), SUPPLY_NODE)[:1] == ["knowledge"], kinds_of(sim(capital=1e9), SUPPLY_NODE))
supply = supply_sim()
check("an unmet supply group is a supply blocker", "supply" in kinds_of(supply, SUPPLY_NODE),
      supply.start_blockers(SUPPLY_NODE))
check("the supply blocker names the options that would serve",
      "mat_manganese" in supply.start_blockers(SUPPLY_NODE)[0]["ids"], supply.start_blockers(SUPPLY_NODE))

staff_sim = sim(capital=1e9)
staff_node = "ag2_botanic_garden"
check("missing craftsmen are a specialists blocker", kinds_of(staff_sim, staff_node)[:1] == ["specialists"],
      staff_sim.start_blockers(staff_node))

political_sim = sim(capital=1e9)
check("a state that is wary is a politics blocker", kinds_of(political_sim, "ag2_chaff_cutter")[:1] == ["politics"],
      political_sim.start_blockers("ag2_chaff_cutter"))

poor_sim = sim(capital=1.0)
startable = [node_id for node_id in NODES if poor_sim.start_reason(node_id)[0]]
dearest = max(startable, key=poor_sim.project_cost)
check("a bill past cash and credit is a money blocker", kinds_of(poor_sim, dearest) == ["money"],
      poor_sim.start_blockers(dearest))

closed_sim = sim(capital=1e9)
closed_sim.done.add("workshop_first")
closed_sim._done_changed()
closed_sim.mothball_work("workshop_first")
check("a built work that was shut is a closed blocker", kinds_of(closed_sim, "workshop_first") == ["closed"],
      closed_sim.start_blockers("workshop_first"))

# --- the refusal and the readout are the same function
check("start_refusal is the first blocker's text",
      supply.start_refusal(SUPPLY_NODE) == supply.start_blockers(SUPPLY_NODE)[0]["text"])
check("a startable node has no blockers", sim(capital=1e9).start_blockers(startable[0]) == [])

# --- why: the kind leads, and every kind is listed
why = S._agent_dispatch(supply, NODES, {"cmd": "why", "id": SUPPLY_NODE})
check("why carries blocked_kind and the blockers list", why.get("blocked_kind") == "supply"
      and [blocker["kind"] for blocker in why.get("blockers", [])] == kinds_of(supply, SUPPLY_NODE), why.get("blockers"))
check("the why screen leads the refusal with its kind", "SUPPLY" in render_why(why), render_why(why)[:600])

# --- compact why: the supply gate is in blocked_by, with its kind
compact = S._agent_dispatch(supply, NODES, {"cmd": "why", "id": SUPPLY_NODE, "compact": True})
check("compact why lists the supply option in blocked_by", "mat_manganese" in compact.get("blocked_by", []), compact)
check("compact why says which kinds block", compact.get("blocked_kinds", [])[:1] == ["supply"], compact)
