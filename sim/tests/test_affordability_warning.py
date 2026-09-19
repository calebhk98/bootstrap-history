"""affordability_warning: regression checks, run individually with `--only affordability_warning`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# THE AGGREGATE AFFORDABILITY WARNING. Five naive playtests, five different
# civilisations, and four of them bankrupted themselves the same way: two or
# three "almost everything rests on this" foundations, each individually
# priced correctly and honestly by `start`'s own "on_credit" forecast, started
# together on a poor_scholar's opening capital. Nothing added them up. These
# checks pin committed_spend()/funding_capacity() (economy.py) - the one
# formula, not two - and the player-facing warning `start` now builds from it.
# =============================================================================

# --- committed_spend() is the exact sum `money` already printed, not a
# second total that could drift from it.
s = sim(capital=400.0)
S._agent_dispatch(s, NODES, {"cmd": "start", "id": "scientific_method"})
S._agent_dispatch(s, NODES, {"cmd": "start", "id": "units_standards"})
_money_agg = S._agent_dispatch(s, NODES, {"cmd": "money"})
check("committed_spend() matches money's own still_owed_on_work_in_hand",
      abs(s.committed_spend() - _money_agg["still_owed_on_work_in_hand"]) < 0.1,
      (s.committed_spend(), _money_agg["still_owed_on_work_in_hand"]))
check("money also states the real financing ceiling, the same number "
      "the aggregate start-time warning uses",
      abs(s.funding_capacity() - _money_agg["you_could_actually_fund_up_to"]) < 0.1,
      (s.funding_capacity(), _money_agg["you_could_actually_fund_up_to"]))

# --- the un-manual director's own start heuristic (step(), core.py) is
# reading committed_spend()/funding_capacity(), not a private copy of the
# same arithmetic that could quietly disagree with it.
#
# BEHAVIOURAL, NOT A SOURCE SCAN: a grep of getsource(Sim.step) concatenated
# with every _step_* phase method, for the two literal call strings
# "self.funding_capacity()" and "self.committed_spend()", depends on step()
# and its phases staying laid out exactly as written the day such a check is
# added - a substring match cannot tell a real call from the same words
# sitting in a comment (test_parallelism_note.py records this failure mode
# actually happening once, to a sibling check in this same style: a split
# left a comment naming the field above the real assignment, and the check
# passed on the comment alone). The actual claim - that the year's
# project-start budget is funding_capacity()
# minus committed_spend(), not a second formula - is directly observable:
# normalise every candidate's project_cost() to one known number, then show
# that a household whose (funding_capacity() - committed_spend()) clears
# that number gets a new project and one whose does not, does not, with
# nothing else about the household different between the two runs.
def _start_room(funding_capacity, committed_spend, project_cost=9000.0):
    """A fresh un-manual household with funding_capacity(), committed_
    spend() and project_cost() all pinned to controlled numbers, stepped
    once. Pinning project_cost() to one number for every candidate removes
    the confound of some candidates costing nothing at all (a few nodes in
    the tree need no denarii, only founder-hours, and those always clear
    any room) - with every candidate priced identically, whether ANYTHING
    starts is governed purely by whether the pinned room clears the pinned
    price."""
    household = sim(capital=1e7, manual=False)
    household.project_cost = lambda node_id: project_cost
    household.funding_capacity = lambda: funding_capacity
    household.committed_spend = lambda: committed_spend
    household.step()
    return household


_room_clears = _start_room(funding_capacity=10000.0, committed_spend=0.0)
check("a household whose funding_capacity() - committed_spend() clears "
      "every candidate's (pinned) project_cost() starts new work this year",
      len(_room_clears.active) > 0, list(_room_clears.active))

_room_short_on_capacity = _start_room(funding_capacity=8000.0, committed_spend=0.0)
check("...and the SAME pinned project_cost, with funding_capacity() alone "
      "trimmed just below it, starts nothing - proving the gate reads "
      "funding_capacity(), not just capital in hand",
      len(_room_short_on_capacity.active) == 0, list(_room_short_on_capacity.active))

_room_short_on_committed = _start_room(funding_capacity=1e7, committed_spend=1e7 - 5000.0)
check("...and a household with huge funding_capacity() but committed_spend() "
      "eating almost all of it also starts nothing - proving the gate reads "
      "committed_spend() too, and does not just check funding_capacity() alone",
      len(_room_short_on_committed.active) == 0, list(_room_short_on_committed.active))

# --- THE ROME OPENING, REPRODUCED EXACTLY: scientific_method (230) then
# units_standards (444) on a poor_scholar's 400 denarii. Individually,
# on_credit correctly says the SECOND start alone only needs to borrow 44 -
# and that figure is honest about that one project. It says nothing about
# scientific_method's own 230 still unpaid and drawing on the identical
# purse the same year, which is the whole of what sank this opening.
s = sim(capital=400.0)
r_sci = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "scientific_method"})
check("set-up: scientific_method alone needed no warning, on 400 denarii",
      r_sci["ok"] and "total_committed_across_active_work" not in r_sci, r_sci)
r_units = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "units_standards"})
check("set-up: on_credit still prices the second start alone, correctly, "
      "at a small gap",
      r_units["ok"] and r_units["on_credit"]["you_would_borrow"] < 100,
      r_units.get("on_credit"))
_agg = r_units.get("total_committed_across_active_work")
check("...but starting the second foundation on top of the first DOES warn "
      "about what both together have committed you to",
      _agg is not None, r_units)
check("...naming the true combined total (both projects' own cost_left), "
      "not just this one project's bill",
      _agg and abs(_agg["you_have_promised"] - (230.0 + 444.0)) < 1.0,
      _agg)
check("...against what is actually held right now, not a padded estimate",
      _agg and abs(_agg["you_currently_hold"] - 400.0) < 1.0, _agg)
check("...and the credit this combination is likely to draw is bigger than "
      "the single-project on_credit forecast alone suggested",
      _agg and _agg["likely_to_draw_on_credit_between_them"]
      > r_units["on_credit"]["you_would_borrow"],
      (_agg, r_units["on_credit"]))
check("...framed as a warning the player can act on, not a refusal",
      r_units["ok"], r_units)

# --- NO WARNING for a single project, however large: the aggregate question
# only makes sense once more than one thing is drawing on the same purse,
# and on_credit above already answers the single-project case on its own.
s = sim(capital=50.0)
s.done.add("sc2_notation_positional")
s._done_changed()
r_one = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "arithmetic_positional"})
check("a single active project never gets the aggregate warning - on_credit "
      "already answers for it alone",
      r_one["ok"] and "total_committed_across_active_work" not in r_one, r_one)

# --- NO WARNING when there is genuinely room: a rich founder starting the
# same two foundations is not walking into anything.
s = sim(capital=1e6)
S._agent_dispatch(s, NODES, {"cmd": "start", "id": "scientific_method"})
r_rich = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "units_standards"})
check("plenty of cash on hand: no aggregate warning even with two things "
      "started together",
      r_rich["ok"] and "total_committed_across_active_work" not in r_rich, r_rich)

# --- `available`'s own front-page advice says the same thing, ONCE, the
# first time a brand-new player looks at the leverage shortlist - not on
# every call, which would bury it in noise.
s = sim(capital=400.0)
_av1 = S._agent_dispatch(s, NODES, {"cmd": "available"})
check("available's leverage list carries the stacking caution the first "
      "time a player sees it",
      bool(_av1.get("most_rests_on_these"))
      and "stacking_several_is_the_trap" in _av1, _av1.get("most_rests_on_these"))
_av2 = S._agent_dispatch(s, NODES, {"cmd": "available"})
check("...and never repeats it on a later call - said once, not nagged",
      "stacking_several_is_the_trap" not in _av2, _av2)
