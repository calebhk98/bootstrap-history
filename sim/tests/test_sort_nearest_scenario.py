"""Scenarios in a whole game for commands that took the sort-key work with them: `stuck` under fog, `rush` (a bulk start, capped
by hours and by limit, fog-safe), the founder's death (its own field, the age, the step stopping, the save and load, the log).
The rules that need no game are in test_sort_nearest; the announcement of staff lost is test_complaint_579_staff_loss_events
and, through the yearly staff step, test_staff_ledger_and_idle_trades_scenario."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of

# One game serves the fog, venture and rush checks.
shared = unopened_sim(capital=5_000_000.0)

# `stuck` says outright, under fog, that it cannot check the goal's route.
shared.fog = True
shared.revealed = set()
stuck_fogged = S._agent_dispatch(shared, NODES, {"cmd": "stuck"})
check("`stuck`, under fog with a goal set, says it cannot check the goal's route",
      "this_does_not_know_your_goal" in stuck_fogged, stuck_fogged.get("this_does_not_know_your_goal"))
shared.fog = False
check("...and says nothing of the kind with fog off, where the goal-aware branch runs",
      "this_does_not_know_your_goal" not in S._agent_dispatch(shared, NODES, {"cmd": "stuck"}),
      "fog off: no such field")
shared.fog = True

# `rush`: a bulk start, capped by hours and by limit, fog-safe.
visible_before_rush = {entry["id"] for entry in S._agent_available(shared, NODES, {"all": True})["available"]}
rush_one = S._agent_dispatch(shared, NODES, {"cmd": "rush", "limit": 1})
rush_many = S._agent_dispatch(shared, NODES, {"cmd": "rush", "limit": 1000})
check("a rush limit caps how many it actually begins", rush_one["count_started"] == 1, rush_one["count_started"])
check("`rush` starts more than one thing in a single call", rush_many.get("count_started", 0) >= 2,
      rush_many.get("count_started"))
check("...and every id it reports started is actually active now",
      all(entry["id"] in shared.active or entry["id"] in shared.done
          for entry in rush_one["started"] + rush_many["started"]),
      [entry["id"] for entry in rush_many["started"]])
check("under fog, the first thing `rush` starts was already on the visible `available` list",
      all(entry["id"] in visible_before_rush for entry in rush_one["started"]),
      [entry["id"] for entry in rush_one["started"] if entry["id"] not in visible_before_rush])
hours_owed = sum(NODES[entry["id"]]["ph"] for entry in rush_many.get("started") or [])
check("`rush` does not commit more hours than a couple of years can hold",
      hours_owed <= shared.labour.director_pool() * 2.0 + max(
          NODES[entry["id"]]["ph"] for entry in (rush_many.get("started") or [{"id": GOAL}])),
      (hours_owed, shared.labour.director_pool()))
check("...and says why it stopped rather than silently starting fewer",
      any("would not make them go faster" in str(entry.get("why")) for entry in (rush_many.get("not_started") or [])),
      [entry.get("why") for entry in (rush_many.get("not_started") or [])][:1])

def without_market(game):
    """The checks below read the founder's own year (death, staff attrition), which the year's market close does not
    feed, and that close is nearly all of a step's cost; leave it out of the games that only step through it."""
    game._step_market = lambda: None
    return game


# The founder's death is legible: its own field with a numeric age, the step stops there, the age
# survives a save and load, and the log says what it means for the run.
mortal = without_market(sim(capital=1_000_000.0, events=True))
mortal.cfg["immortal"] = False
mortal.life_left = 1.0
mortal.end_year = mortal.cfg["start_year"] + 200
step_reply = S._agent_dispatch(mortal, NODES, {"cmd": "step", "years": 150})
died = step_reply.get("the_founder_died_this_step")
check("the founder's death gets a field of its own in the step that carries it",
      isinstance(died, dict), died)
check("...and the age is a number you can read", isinstance((died or {}).get("aged_about"), int), died)
check("...and `state` carries the age from then on",
      step_reply.get("founder_died_aged") == (died or {}).get("aged_about"),
      (step_reply.get("founder_died_aged"), died))
check("...and the step stopped there instead of running the requested years past it",
      step_reply["year"] < mortal.cfg["start_year"] + 150, step_reply["year"])
session_path = os.path.join(ROOT, _rel("founder_death.json"))
S.save_state(mortal, session_path)
reloaded = unopened_sim()
S.load_state(reloaded, session_path)
reloaded_state = S._agent_dispatch(reloaded, NODES, {"cmd": "state"})
check("the founder's age at death survives a save and a fresh process loading it back",
      reloaded_state.get("founder_died_aged") == step_reply.get("founder_died_aged")
      and reloaded_state.get("founder_died_aged") is not None,
      (reloaded_state.get("founder_died_aged"), step_reply.get("founder_died_aged")))
for _ in range(2):  # the countdown is logged in the second year after the death
    mortal.step()
check("the founder's death says what it means for the run, not only that it happened",
      any(cause_of(message) == "founder_dies" and not facts_of(message)["deputies_carry_the_work"]
          for _, message in mortal.log),
      [message for _, message in mortal.log if "FOUNDER DIES" in message][:1])
check("...and the programme dissolving is counted down where a player sees it",
      any(cause_of(message) == "programme_dissolving"
          and facts_of(message)["run_ends_after_years"] == mortal.DISSOLUTION_YEARS_UNTIL_END
          for _, message in mortal.log),
      [message for _, message in mortal.log if "DISSOLVING" in message][:1])
