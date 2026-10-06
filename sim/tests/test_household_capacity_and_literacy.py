"""How many people a household can feed, house and oversee at all
(household_room, the founder's own deputised hours), the advice that points
at what would widen it, and the separate ceiling literacy puts on lettered
trades.

Regrouped from test_round8_fixes.py and test_round9.py - see CLAUDE.md's
test-file reorganisation note. Checks moved verbatim; each one's own comment
explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- the ceiling on lettered trades and the household-room refusals, on one rich game; checks that
# need the starting literacy come before the technologies that widen it.
core = sim(capital=2000000.0)

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
_ok_el, _why_el = core.labour.train("electrician", 20)
check("...so twenty electricians cannot be taught into a society of twelve",
      not _ok_el and "literacy" in str(_why_el), _why_el)

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
check("a trade that needs no letters is not capped by literacy at all",
      core.labour.literate_capacity("smith") == float("inf"), core.labour.literate_capacity("smith"))

# household_room bounds hire, buy and train by one number. The literacy ceiling is already widened,
# so the room is what binds.
_room0 = core.labour.household_room()
check("a fresh household has room for a few people and no more", 0 < _room0 < 20, _room0)
check("...and the literacy ceiling is not what binds here",
      core.labour.literate_capacity("machinist") > _room0 + 1, (core.labour.literate_capacity("machinist"), _room0))
_ok_within, _why_within = sim(capital=2000000.0).labour.train("machinist", 1)
check("teaching within the room still works", _ok_within, _why_within)
core.labour.hire("smith", int(_room0))          # fill the room exactly
_ok_t3, _why_t3 = core.labour.train("machinist", 1)
check("teaching past what you can feed and house is refused",
      not _ok_t3 and "feed, house and oversee" in _why_t3, _why_t3)
check("...and it says there is no room for even one", "no room for even one" in _why_t3, _why_t3)
check("...and what makes room, which is not what buys people", "built" in _why_t3, _why_t3)
check("hire, buy and train are all bounded by the same one number",
      core.labour.hire("smith", 1)[0] is False and core.labour.train("machinist", 1)[0] is False
      and core.labour.buy_slaves(1) <= 0, (_room0, core.labour.household_room()))

# --- advice on how to get artisans, scholars and room never points at a remedy waiting on what it
# supplies, and offers a shut institution back as the cheap fix.
advice = sim(capital=1000000.0)
check("giving staff advice does not recurse into itself",
      isinstance(advice.start_reason("workshop_first")[1], str), "no RecursionError")
advice.done.add("patron_local"); advice._done_changed()
_adv = advice.labour._staff_advice("artisans")
check("advice never points at a remedy waiting on the thing it supplies",
      "workshop_first" not in _adv or "waiting on artisans" in _adv, _adv)
advice.artisans = 20.0
check("...and names it plainly once it is actually reachable",
      "waiting on artisans" not in advice.labour._staff_advice("artisans"), advice.labour._staff_advice("artisans"))
run_it(advice, "workshop_first", "school_founded")
_advice_open = advice.labour._room_advice()
advice.operating.discard("school_founded")
_advice_shut = advice.labour._room_advice()
check("a shut room-source is offered back as the cheap fix, not silently dropped from the advice",
      "school_founded" in _advice_shut and "reopen" in _advice_shut.lower(), _advice_shut)
check("...and it is not also still claimed as an open place in the same breath",
      "school_founded" not in _advice_open or "reopen" not in _advice_open.lower(),
      (_advice_open, _advice_shut))
_staff_shut = advice.labour._staff_advice("scholars")
check("the scholar-pool advice offers to reopen a shut school rather than treating it as covered",
      "school_founded" in _staff_shut and "reopen" in _staff_shut.lower(), _staff_shut)
check("ROOM_SOURCES names real node ids only - no stale reference silently filtered out",
      all(node_id in NODES for node_id, _ in advice.ROOM_SOURCES),
      [node_id for node_id, _ in advice.ROOM_SOURCES if node_id not in NODES])
advice.done.update(NODES); advice._done_changed()
# Open, not just built: every room source must be running for "you have everything".
advice.operating.update(node_id for node_id, _ in advice.ROOM_SOURCES if node_id in NODES)
check("...and says so plainly when you already hold every one of them",
      "every one of them" in advice.labour._room_advice(), advice.labour._room_advice())

# --- a deputy is announced with what it does to the founder's year, once per whole deputy.
def _deputies_are_announced():
    deputies_sim = sim(capital=2000000.0, manual=False)
    run_it(deputies_sim, "school_founded", "patron_imperial", "academy_network")
    for _ in range(12):
        deputies_sim.step()
        if any("deput" in message and "your year is" in message for _, message in deputies_sim.log):
            break
    said = [message for _, message in deputies_sim.log if "deput" in message]
    return (any("deput" in message and "your year is" in message for _, message in deputies_sim.log)
            and len(said) <= int(deputies_sim.directors_extra) + 1, said[:1])

slow_check("gaining a deputy is announced with what it does to your year, "
           "once per whole deputy rather than every year",
           _deputies_are_announced)
