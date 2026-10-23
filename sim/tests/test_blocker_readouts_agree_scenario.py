"""SMOKE: an unopened game reaches the blocker rule (`sim/engine/blockers.py`, rule tests in `test_blockers_rule`) and every readout agrees: one classifier names every blocker: Complaints/125, 263 (and 234, 238, 239, 268 below)."""
from .harness import *  # noqa: F401,F403

SUPPLY_NODE = "mat_bulk_steel"


def supply_sim():
	test_sim = unopened_sim(capital=1e9)
	test_sim.done.update(NODES[SUPPLY_NODE]["pre"])
	test_sim._done_changed()
	return test_sim


def kinds_of(test_sim, node_id):
	return [blocker["kind"] for blocker in test_sim.start_blockers(node_id)]


supply = supply_sim()

# --- the refusal and the readout are the same function
check("start_refusal is the first blocker's text",
      supply.start_refusal(SUPPLY_NODE) == supply.start_blockers(SUPPLY_NODE)[0]["text"])
# --- why: the kind leads, and every kind is listed (the rendering is checked where presentation is)
why = S._agent_dispatch(supply, NODES, {"cmd": "why", "id": SUPPLY_NODE})
check("why carries blocked_kind and the blockers list", why.get("blocked_kind") == "supply"
      and [blocker["kind"] for blocker in why.get("blockers", [])] == kinds_of(supply, SUPPLY_NODE), why.get("blockers"))

# --- compact why: the supply gate is in blocked_by, with its kind
compact = S._agent_dispatch(supply, NODES, {"cmd": "why", "id": SUPPLY_NODE, "compact": True})
check("compact why lists the supply option in blocked_by", "mat_manganese" in compact.get("blocked_by", []), compact)
check("compact why says which kinds block", compact.get("blocked_kinds", [])[:1] == ["supply"], compact)
