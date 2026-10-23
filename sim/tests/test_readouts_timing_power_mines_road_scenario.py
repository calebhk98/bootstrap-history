"""Scenario (Complaints/230 and 264): on a running game the quoted finish matches a stepped run, `why` quotes it, and
`available` marks what lies on the road to the goal. The schedule, power, mine and road rules are in
test_readouts_timing_power_mines_road."""
from .harness import *  # noqa: F401,F403

# ===========================================================================
# Complaints/230: the quoted finish is the earliest the payment schedule allows
# ===========================================================================
SLOW_NODE = "civ_sewer_separate"


def stepped_completion(reputation):
	test_sim = unopened_sim(capital=1e12)
	test_sim.state.household.reputation = reputation
	saved_risk = test_sim.nodes[SLOW_NODE]["risk"]
	test_sim.nodes[SLOW_NODE]["risk"] = 0.0
	try:
		quoted = test_sim.earliest_completion_years(SLOW_NODE)
		test_sim.start_project(SLOW_NODE)
		seat = test_sim.playing_seats()[0]
		for steps in range(1, 40):
			# The year's project work and the calendar, without the economy around it (money is not the limit here).
			with test_sim.act_as(seat):
				test_sim.begin_seat_year()
				test_sim.begin_world_year()
				test_sim._run_seat_work()
			test_sim.state.scenario.year += 1
			if SLOW_NODE in test_sim.done:
				return quoted, steps
	finally:
		test_sim.nodes[SLOW_NODE]["risk"] = saved_risk
	return quoted, None


quoted_years, real_steps = stepped_completion(80)
check("the quoted earliest completion matches the steps a clean run takes",
      real_steps is not None and real_steps - 1 < quoted_years <= real_steps, (quoted_years, real_steps))
reputation_sim = unopened_sim(capital=1e12)
reputation_sim.state.household.reputation = 80
why_timing = S._agent_dispatch(reputation_sim, NODES, {"cmd": "why", "id": SLOW_NODE})
check("why quotes the earliest completion year count and calendar year",
      why_timing.get("earliest_completion_years") == round(reputation_sim.earliest_completion_years(SLOW_NODE), 2)
      and isinstance(why_timing.get("earliest_completion_year"), (int, float)),
      why_timing.get("earliest_completion_years"))
check("the retry expectation is never below the earliest completion",
      reputation_sim.expected_calendar_years(SLOW_NODE) >= reputation_sim.earliest_completion_years(SLOW_NODE) - 1e-9)


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
