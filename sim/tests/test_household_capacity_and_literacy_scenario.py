"""Scenarios (Complaint 640; the rules are in test_household_capacity_and_literacy and test_staff_advice_rules): the
household room, the literacy ceiling and the advice, reached through the player's commands on a whole game."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of


# --- the ceiling on lettered trades and the household-room refusals, on one rich game; checks that
# need the starting literacy come before the technologies that widen it.
core = unopened_sim(capital=2000000.0)

# A lettered trade shows the ceiling on how many can ever exist here, and `why` warns when a node
# wants more than can ever exist.
_labour_scholar = S._agent_dispatch(core, NODES, {"cmd": "labour", "trade": "scholar"})
_labour_smith = S._agent_dispatch(core, NODES, {"cmd": "labour", "trade": "smith"})
_why_goal = S._agent_dispatch(core, NODES, {"cmd": "why", "id": GOAL})
_why_easy = S._agent_dispatch(core, NODES, {"cmd": "why", "id": "horse_collar"})
check("a lettered trade shows the ceiling on how many can ever exist here",
      _labour_scholar["trade"].get("most_this_society_can_ever_supply") is not None,
      _labour_scholar["trade"].get("most_this_society_can_ever_supply"))
check("...and says what widens it",
      "printing" in str(_labour_scholar["trade"].get("what_widens_it")),
      _labour_scholar["trade"].get("what_widens_it"))
check("...and a trade needing no letters carries no such ceiling",
      _labour_smith["trade"].get("most_this_society_can_ever_supply") is None,
      _labour_smith["trade"].get("most_this_society_can_ever_supply"))
check("and `why` warns when a node wants more scholars than can ever exist",
      _why_goal.get("more_scholars_than_this_society_can_supply"),
      _why_goal.get("more_scholars_than_this_society_can_supply"))
check("...and more craftsmen than the household could ever hold",
      _why_goal.get("more_craftsmen_than_your_household_can_hold"),
      _why_goal.get("more_craftsmen_than_your_household_can_hold"))
check("...and says nothing of the kind about a node you could staff",
      not _why_easy.get("more_scholars_than_this_society_can_supply"),
      _why_easy.get("more_scholars_than_this_society_can_supply"))

# `train electrician 20` is bounded by literacy like every other taught trade.
check("every taught trade is bounded by literacy, electrician included",
      all(trade in core.labour.LITERATE_TRADES for trade in S.TRADES_ABSENT),
      sorted(set(S.TRADES_ABSENT) - set(core.labour.LITERATE_TRADES)))
# The household-room refusal names what raises the room, not what buys people.
_ok_rm, _why_rm = core.labour.hire("smith", 20)
check("a room refusal names what raises the room, not what buys people",
      not _ok_rm and "built" in _why_rm and "hire" not in _why_rm.split(".")[1],
      _why_rm)
check("...and names the nearest of them first, not the largest",
      _why_rm.index("workshop_first") < (_why_rm.find("school_founded") if "school_founded" in _why_rm else len(_why_rm)),
      _why_rm[_why_rm.index("built"):][:120])

# Teaching a society to read raises what it can staff, but not without bound.
_cap0 = core.labour.literate_capacity("machinist")
for _k in ("rag_paper", "printing_press", "if_movable_type", "school_founded",
           "academy_network", "corpus_written"):
    if _k in NODES:
        core.apply_tech_effects(_k)
_cap1 = core.labour.literate_capacity("machinist")
check("teaching a society to read raises what it can staff", _cap1 > _cap0 * 1.5, (_cap0, _cap1))
check("...but not without bound", _cap1 < _cap0 * 5, (_cap0, _cap1))
# household_room bounds hire, buy and train by one number. The literacy ceiling is already widened,
# so the room is what binds.
_room0 = core.labour.household_room()
check("a fresh household has room for a few people and no more", 0 < _room0 < 20, _room0)
check("...and the literacy ceiling is not what binds here",
      core.labour.literate_capacity("machinist") > _room0 + 1, (core.labour.literate_capacity("machinist"), _room0))
_ok_within, _why_within = unopened_sim(capital=2000000.0).labour.train("machinist", 1)
check("teaching within the room still works", _ok_within, _why_within)
core.labour.hire("smith", int(_room0))          # fill the room exactly
_ok_t3, _why_t3 = core.labour.train("machinist", 1)
check("teaching past what you can feed and house is refused",
      not _ok_t3 and cause_of(_why_t3) == "household_room", _why_t3)
check("...and it says there is no room for even one", core.labour.household_room() < 1.0, core.labour.household_room())
check("...and what makes room, which is not what buys people",
      facts_of(_why_t3)["remedies"]
      and all(remedy["action"] in ("buy_housing", "reopen", "build") for remedy in facts_of(_why_t3)["remedies"]),
      facts_of(_why_t3))
check("hire, buy and train are all bounded by the same one number",
      core.labour.hire("smith", 1)[0] is False and core.labour.train("machinist", 1)[0] is False
      and core.labour.buy_slaves(1) <= 0, (_room0, core.labour.household_room()))

# --- the staff advice itself is test_staff_advice_rules; here it is read through the real game's room sources and
# the start reason that calls it.
advice = unopened_sim(capital=1000000.0)
check("giving staff advice does not recurse into itself",
      isinstance(advice.start_reason("workshop_first")[1], str), "no RecursionError")
check("ROOM_SOURCES names real node ids only - no stale reference silently filtered out",
      all(node_id in NODES for node_id, _ in advice.ROOM_SOURCES),
      [node_id for node_id, _ in advice.ROOM_SOURCES if node_id not in NODES])

_DEPUTY_YEARS = 2


# --- a deputy is announced with what it does to the founder's year, once per whole deputy.
def _deputies_are_announced():
    deputies_sim = sim(capital=20000000.0, manual=False)   # the opening purse is re-expressed in the game money unit, so this buys what the old figure did
    run_it(deputies_sim, "school_founded", "patron_imperial", "academy_network")
    peak_deputies = 0.0
    for _ in range(_DEPUTY_YEARS):
        deputies_sim.step()
        peak_deputies = max(peak_deputies, deputies_sim.directors_extra)
    said = [message for _, message in deputies_sim.log if "deput" in message]
    # deputies can leave again, so the bound is the most held at once, not the count at the end
    return (any("your year is" in message for message in said)
            and len(said) == len(set(said)) and len(said) <= int(peak_deputies), said[:1])

slow_check("gaining a deputy is announced with what it does to your year, "
           "once per whole deputy rather than every year",
           _deputies_are_announced)
