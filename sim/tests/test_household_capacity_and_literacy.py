"""How many people a household can feed, house and oversee at all
(household_room, the founder's own deputised hours), the advice that points
at what would widen it, and the separate ceiling literacy puts on lettered
trades.

Regrouped from test_round8_fixes.py and test_round9.py - see CLAUDE.md's
test-file reorganisation note. Checks moved verbatim; each one's own comment
explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: the advice on how to get artisans said "build workshop_first (you
# need somewhere for them to work)" while `why workshop_first` said it was
# blocked for want of artisans. A play tester quoted the two lines at each
# other.
s_circ = sim()
s_circ.done.add("patron_local"); s_circ._done_changed()
_adv = s_circ._staff_advice("artisans")
check("advice never points at a remedy waiting on the thing it supplies",
      "workshop_first" not in _adv or "waiting on artisans" in _adv, _adv)
s_circ.artisans = 20.0
check("...and names it plainly once it is actually reachable",
      "waiting on artisans" not in s_circ._staff_advice("artisans"),
      s_circ._staff_advice("artisans"))
check("giving that advice does not recurse into itself",
      isinstance(sim().start_reason("workshop_first")[1], str), "no RecursionError")

# --- BREAK: the founder's year quietly grew from 2,000 hours to 10,175 and
# nothing ever said so - the largest change to the resource the game is built
# on, noticed by accident.
def _deputies_are_announced():
    deputies_sim = sim(capital=2000000.0, manual=False)
    run_it(deputies_sim, "school_founded", "patron_imperial", "academy_network")
    for _ in range(30):
        deputies_sim.step()
    said = [message for _, message in deputies_sim.log if "deput" in message]
    return (any("deput" in message and "your year is" in message for _, message in deputies_sim.log)
            and len(said) <= int(deputies_sim.directors_extra) + 1, said[:1])

slow_check("gaining a deputy is announced with what it does to your year, "
           "once per whole deputy rather than every year",
           _deputies_are_announced)

# --- BREAK: "this society's literacy will not supply more than 5.9 scholars
# in total, ever, at any price" - and it never moved, through paper, printing,
# a university and three academies. The factor was clamped at 1.0 and Rome
# starts AT the reference, so for Rome the whole mechanism was inert.
s_lit = sim()
_cap0 = s_lit.literate_capacity("machinist")
for _k in ("rag_paper", "printing_press", "if_movable_type", "school_founded",
           "academy_network", "corpus_written"):
    if _k in NODES:
        s_lit.apply_tech_effects(_k)
_cap1 = s_lit.literate_capacity("machinist")
check("teaching a society to read raises what it can staff",
      _cap1 > _cap0 * 1.5, (_cap0, _cap1))
check("...but not without bound",
      _cap1 < _cap0 * 5, (_cap0, _cap1))
check("a trade that needs no letters is not capped by literacy at all",
      s_lit.literate_capacity("smith") == float("inf"),
      s_lit.literate_capacity("smith"))
# --- BREAK: `train electrician 20` gave 27 while machinists stopped at 5.9.
check("every taught trade is bounded by literacy, electrician included",
      not (set(S.Sim.LITERATE_TRADES) ^ set(S.Sim.LITERATE_TRADES))
      and all(trade in S.Sim.LITERATE_TRADES for trade in S.TRADES_ABSENT),
      sorted(set(S.TRADES_ABSENT) - set(S.Sim.LITERATE_TRADES)))
s_el = sim(capital=2000000.0)
_ok_el, _why_el = s_el.train("electrician", 20)
check("...so twenty electricians cannot be taught into a society of twelve",
      not _ok_el and "literacy" in str(_why_el), _why_el)

# --- BREAK: the household-room refusal handed back the advice for BUYING
# people, every word of which needs room you do not have. A play tester with a
# ceiling of 166.9 against a node wanting 200 craftsmen wrote that none of the
# three remedies the message suggests works.
s_rm = sim(capital=1000000.0)
_ok_rm, _why_rm = s_rm.hire("smith", 20)
check("a room refusal names what raises the room, not what buys people",
      not _ok_rm and "built" in _why_rm and "hire" not in _why_rm.split(".")[1],
      _why_rm)
check("...and names the nearest of them first, not the largest",
      _why_rm.index("workshop_first") < _why_rm.index("school_founded"),
      _why_rm[_why_rm.index("built"):][:120])
s_rm2 = sim(capital=1000000.0)
s_rm2.done.update(NODES); s_rm2._done_changed()
# OPEN, not just built: a ROOM_SOURCES entry that is done but not operating
# is exactly the case the next block tests (reopen advice, not "you have
# everything"), so "every one of them" has to mean everything built AND
# running, the same distinction run_it exists to set up everywhere else.
s_rm2.operating.update(node_id for node_id, _ in s_rm2.ROOM_SOURCES if node_id in NODES)
check("...and says so plainly when you already hold every one of them",
      "every one of them" in s_rm2._room_advice(), s_rm2._room_advice())

# --- BREAK: a ROOM_SOURCES institution built and then SHUT (attrition, a
# bad year, or the player's own `mothball`) vanished from this advice
# entirely - filtered out for being `in self.done`, exactly like something
# never built, even though staff_capacity() had already stopped counting
# its places the moment it closed. The advice recommended building a new,
# dearer institution instead of reopening the one already paid for.
s_rm3 = sim(capital=1000000.0)
run_it(s_rm3, "workshop_first", "school_founded")
_advice_open = s_rm3._room_advice()
s_rm3.operating.discard("school_founded")
_advice_shut = s_rm3._room_advice()
check("a shut room-source is offered back as the cheap fix, not silently "
      "dropped from the advice",
      "school_founded" in _advice_shut and "reopen" in _advice_shut.lower(),
      _advice_shut)
check("...and it is not also still claimed as an open place in the same "
      "breath",
      "school_founded" not in _advice_open or "reopen" not in _advice_open.lower(),
      (_advice_open, _advice_shut))

# --- and the same fix, for the scholar/artisan hiring-pool advice
# (_staff_advice / STAFF_SOURCES), which has its own, separate list.
s_sa = sim(capital=1000000.0)
run_it(s_sa, "school_founded")
s_sa.operating.discard("school_founded")
_staff_shut = s_sa._staff_advice("scholars")
check("the scholar-pool advice offers to reopen a shut school rather than "
      "silently treating it as already covered",
      "school_founded" in _staff_shut and "reopen" in _staff_shut.lower(),
      _staff_shut)

# --- BREAK: ROOM_SOURCES carried a stale id, "bessemer_openhearth", which
# does not exist in the tree (the real id is met_open_hearth_furnace) -
# STAFF_CAPACITY_SOURCES was corrected to the real id and this second,
# separate table was not, so the 65 places an open-hearth furnace is worth
# were never once offered as advice even though the arithmetic (via
# staff_capacity) already counted them correctly.
check("ROOM_SOURCES names real node ids only - no stale reference silently "
      "filtered out of every reply that reads this table",
      all(node_id in NODES for node_id, _ in s_rm3.ROOM_SOURCES),
      [node_id for node_id, _ in s_rm3.ROOM_SOURCES if node_id not in NODES])

# --- BREAK: household_room exists because `hire` and `buy` used different
# numbers. `train` was the third verb and checked nothing at all, so the
# optimizer taught its way to a headcount of 26.9 against room for 6 - minus
# eighteen places - and then could not hire the artisans to supervise
# anything.
s_tr3 = sim(capital=2000000.0)
# Widen the literacy ceiling first, so the ROOM is what binds rather than the
# pool of people who can read - the tightest constraint should be the one that
# speaks, and here we are testing the other one.
for _k in ("rag_paper", "printing_press", "if_movable_type", "academy_network"):
    if _k in NODES:
        s_tr3.apply_tech_effects(_k)
_room0 = s_tr3.household_room()
check("a fresh household has room for a few people and no more",
      0 < _room0 < 20, _room0)
check("...and the literacy ceiling is not what binds here",
      s_tr3.literate_capacity("machinist") > _room0 + 1,
      (s_tr3.literate_capacity("machinist"), _room0))
# Fill the household first, which is the state the tester was in: the hours
# check bites long before the room does at any larger number, because teaching
# costs 450 founder-hours a head.
s_tr3.hire("smith", int(_room0))
_ok_t3, _why_t3 = s_tr3.train("machinist", 1)
check("teaching past what you can feed and house is refused",
      not _ok_t3 and "feed, house and oversee" in _why_t3, _why_t3)
check("...and it says there is no room for even one",
      "no room for even one" in _why_t3, _why_t3)
check("...and what makes room, which is not what buys people",
      "built" in _why_t3, _why_t3)
s_tr4 = sim(capital=2000000.0)
check("...and teaching within the room still works",
      s_tr4.train("machinist", 1)[0], s_tr4.train("machinist", 1)[1])
# The three verbs must agree, which is the whole reason household_room exists.
s_ag = sim(capital=2000000.0)
_r = s_ag.household_room()
s_ag.hire("smith", int(_r))          # fill it exactly
check("hire, buy and train are all bounded by the same one number",
      s_ag.hire("smith", 1)[0] is False
      and s_ag.train("machinist", 1)[0] is False
      and s_ag.buy_slaves(1) <= 0,
      (_r, s_ag.household_room()))

# --- BREAK: "this society's literacy will not supply more than 6.4 scholars
# in total, ever" gates the GOAL, which wants twenty-five, and appeared in no
# screen at all: a play tester found it in a refusal message in year 463 of a
# 500-year game. The single thing that decided whether their run could be won.
_rl3, _, _ = proto([{"cmd": "labour", "trade": "scholar"},
                    {"cmd": "labour", "trade": "smith"},
                    {"cmd": "why", "id": GOAL}])
check("a lettered trade shows the ceiling on how many can ever exist here",
      _rl3[0]["trade"].get("most_this_society_can_ever_supply") is not None,
      _rl3[0]["trade"].get("most_this_society_can_ever_supply"))
check("...and says what widens it",
      "printing" in str(_rl3[0]["trade"].get("what_widens_it")),
      _rl3[0]["trade"].get("what_widens_it"))
check("...and a trade needing no letters carries no such ceiling",
      _rl3[1]["trade"].get("most_this_society_can_ever_supply") is None,
      _rl3[1]["trade"].get("most_this_society_can_ever_supply"))
check("and `why` warns when a node wants more scholars than can ever exist",
      _rl3[2].get("more_scholars_than_this_society_can_supply"),
      _rl3[2].get("more_scholars_than_this_society_can_supply"))
check("...and more craftsmen than the household could ever hold",
      _rl3[2].get("more_craftsmen_than_your_household_can_hold"),
      _rl3[2].get("more_craftsmen_than_your_household_can_hold"))
_rl4, _, _ = proto([{"cmd": "why", "id": "horse_collar"}])
check("...and says nothing of the kind about a node you could staff",
      not _rl4[0].get("more_scholars_than_this_society_can_supply"),
      _rl4[0].get("more_scholars_than_this_society_can_supply"))
