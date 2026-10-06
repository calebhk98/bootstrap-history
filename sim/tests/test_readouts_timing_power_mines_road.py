"""Readouts agree with the engine's own checks: Complaints/230, 234, 235, 264."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.economy import _power_status

# ===========================================================================
# Complaints/230: the quoted finish is the earliest the payment schedule allows
# ===========================================================================
SLOW_NODE = "civ_sewer_separate"


def stepped_completion(reputation):
	test_sim = sim(capital=1e12)
	test_sim.state.household.reputation = reputation
	saved_risk = test_sim.nodes[SLOW_NODE]["risk"]
	test_sim.nodes[SLOW_NODE]["risk"] = 0.0
	try:
		quoted = test_sim.earliest_completion_years(SLOW_NODE)
		test_sim.start_project(SLOW_NODE)
		for steps in range(1, 40):
			test_sim.step()
			if SLOW_NODE in test_sim.done:
				return quoted, steps
	finally:
		test_sim.nodes[SLOW_NODE]["risk"] = saved_risk
	return quoted, None


quoted_years, real_steps = stepped_completion(80)
check("the quoted earliest completion matches the steps a clean run takes",
      real_steps is not None and real_steps - 1 < quoted_years <= real_steps, (quoted_years, real_steps))
reputation_sim = sim(capital=1e12)
reputation_sim.state.household.reputation = 80
check("the calendar floor alone stays shorter than the payment schedule",
      reputation_sim.calendar_floor(SLOW_NODE) < reputation_sim.earliest_completion_years(SLOW_NODE))
why_timing = S._agent_dispatch(reputation_sim, NODES, {"cmd": "why", "id": SLOW_NODE})
check("why quotes the earliest completion year count and calendar year",
      why_timing.get("earliest_completion_years") == round(reputation_sim.earliest_completion_years(SLOW_NODE), 2)
      and isinstance(why_timing.get("earliest_completion_year"), (int, float)),
      why_timing.get("earliest_completion_years"))
check("the retry expectation is never below the earliest completion",
      reputation_sim.expected_calendar_years(SLOW_NODE) >= reputation_sim.earliest_completion_years(SLOW_NODE) - 1e-9)


# ===========================================================================
# Complaints/234: a capability flag is labelled as knowledge and shows the kW behind it
# ===========================================================================
power_sim = reputation_sim
power_sim.done.update({"cap_power_water", "cap_power_electric", "power_grid", "cap_power_grid"})
power_sim._done_changed()
tiers = {tier["id"]: tier for tier in _power_status(power_sim, NODES)["power_tiers_you_have_discovered"]}
check("a grid capability with no station reports zero installed generation",
      tiers["cap_power_grid"]["built"] and tiers["cap_power_grid"]["installed_kw"] == 0.0, tiers.get("cap_power_grid"))
check("a built tier with nothing installed says so",
      tiers["cap_power_grid"].get("no_generation_installed") is True, tiers.get("cap_power_grid"))
power_sim.done.add("en_alternator")
power_sim._done_changed()
tiers = {tier["id"]: tier for tier in _power_status(power_sim, NODES)["power_tiers_you_have_discovered"]}
check("generation installed under a tier is counted against that tier",
      tiers["cap_power_steam"]["installed_kw"] > 0, tiers.get("cap_power_steam"))
gate_sim = sim(capital=1e9)
gate_sim.done.update({"en_alternator"})
gate_sim._done_changed()
needs_electric = next(node_id for node_id, node in NODES.items()
                      if "cap_power_electric" in node["pre"] and node_id not in gate_sim.done)
knowledge_blocker = next(blocker for blocker in gate_sim.start_blockers(needs_electric)
                         if blocker["kind"] == "power")
check("a power capability gate says installed generation does not satisfy it",
      "installed" in knowledge_blocker["text"] and "knowledge" in knowledge_blocker["text"], knowledge_blocker)


# ===========================================================================
# Complaints/235: a mine already being sunk is subtracted from the shortfall
# ===========================================================================
mine_sim = reputation_sim
before = mine_sim.shortage_remedy_plan("coal", 100.0)
check("set-up: with nothing sunk the plan proposes the full mine", "buy mine coal 100" in before["commands"], before)
ready_year = int(mine_sim.state.scenario.year) + 3
mine_sim.state.economy.mine_tranches = [["coal", 100.0, ready_year, 1000.0]]
after = mine_sim.shortage_remedy_plan("coal", 100.0)
check("a mine already being sunk is not recommended again", not after["commands"], after)
check("the plan says the commissioned tonnage and the year it is ready",
      "already being sunk" in after["text"] and str(ready_year) in after["text"], after["text"])
mine_sim.state.economy.mine_tranches = [["coal", 40.0, ready_year, 400.0]]
partial = mine_sim.shortage_remedy_plan("coal", 100.0)
check("only the tonnage still uncovered is proposed", "buy mine coal 60" in partial["commands"], partial)


# ===========================================================================
# Complaints/264: a fog-safe marker for what lies on the road to the goal
# ===========================================================================
road_sim = reputation_sim
road_available = S._agent_dispatch(road_sim, NODES, {"cmd": "available", "all": True, "limit": 100})
rows = road_available.get("startable") or road_available.get("available") or []
check("set-up: available has rows", bool(rows), list(road_available)[:12])
check("every startable row says whether it is on the road to the goal",
      all(isinstance(row.get("on_road_to_goal"), bool) for row in rows), rows[:1])
check("some startable rows are on the road and some are not",
      {row.get("on_road_to_goal") for row in rows} == {True, False})
check("supplies and capabilities carry their own mark",
      all(row.get("is_supply_or_capability") == (NODES[row["id"]]["cat"] in ("material", "capability"))
          for row in rows))
