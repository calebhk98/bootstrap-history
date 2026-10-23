"""SCENARIO (affordability warning): five naive playtests bankrupted themselves by starting two or three "almost everything
rests on this" foundations together on a poor scholar's opening capital. In the Rome opening, `start`, `money` and
`available` read committed_spend() and funding_capacity() as one formula, `start` warns of the combined total, and the
director's start gate reads the same two numbers. The warning's rule and the funding parts are in
test_affordability_warning."""
from .harness import *  # noqa: F401,F403


# --- scenario: the Rome opening starts two foundations on a poor purse; `money` and `available` read the same numbers
s = unopened_sim(capital=400.0, surveyed=())
S._agent_dispatch(s, NODES, {"cmd": "start", "id": "scientific_method"})
S._agent_dispatch(s, NODES, {"cmd": "start", "id": "mt2_sintering_process"})
_money = S._agent_dispatch(s, NODES, {"cmd": "money"})
_av1 = S._agent_dispatch(s, NODES, {"cmd": "available"})
_av2 = S._agent_dispatch(s, NODES, {"cmd": "available"})
check("scenario: `money` states committed_spend() and the real financing ceiling the warning uses; `available`'s leverage "
      "list carries the stacking caution the first time a player sees it and never again",
      abs(s.committed_spend() - _money["still_owed_on_work_in_hand"]) < 0.1
      and abs(s.funding_capacity() - _money["you_could_actually_fund_up_to"]) < 0.1
      and bool(_av1.get("most_rests_on_these")) and "stacking_several_is_the_trap" in _av1
      and "stacking_several_is_the_trap" not in _av2,
      (s.committed_spend(), _money["still_owed_on_work_in_hand"], s.funding_capacity(), _money["you_could_actually_fund_up_to"]))

# The Rome opening: scientific_method then mt2_sintering_process on a purse that covers the second alone only just
# short. on_credit prices the second start alone; the warning also counts the first's unpaid cost.
_probe = unopened_sim(surveyed=())
_sci_cost = _probe.project_cost("scientific_method")
_units_cost = _probe.project_cost("mt2_sintering_process")
_purse = round(_units_cost) - 44.0     # just short of the second project alone
s = unopened_sim(surveyed=())
s.market_credit_room = lambda actor_id: None    # the household's own standing sets the line; the opening's loan book is fully lent to others
s.capital = _purse      # in the game's own money, the unit project_cost is quoted in
r_sci = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "scientific_method"})
r_units = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "mt2_sintering_process"})
_agg = r_units.get("total_committed_across_active_work")
# Materials due at the start are paid then (into stock), so what is still owed plus what left the purse for materials
# is the two projects' full cost.
check("scenario: starting a second foundation on a purse just short of it warns, apart from on_credit pricing it alone, "
      "of the true combined total against what is held now; the first alone did not warn",
      r_sci["ok"] and "total_committed_across_active_work" not in r_sci
      and r_units["ok"] and r_units["on_credit"]["you_would_borrow"] < 100 and _agg is not None
      and abs(_agg["you_have_promised"] + (_purse - s.capital) - (_sci_cost + _units_cost)) < 1.0
      and abs(_agg["you_currently_hold"] - s.capital) < 1.0
      and _agg["likely_to_draw_on_credit_between_them"] > r_units["on_credit"]["you_would_borrow"],
      (_agg, r_units.get("on_credit")))

# --- scenario: the un-manual director's start heuristic reads committed_spend()/funding_capacity(), not a private copy.
# Every candidate's project_cost() is pinned to one number, so whether anything starts is governed purely by whether
# the pinned room (funding_capacity() less committed_spend()) clears the pinned price.
def _start_room(funding_capacity, committed_spend, project_cost=9000.0, whole_year=False):
    household = unopened_sim(capital=1e7, manual=False, surveyed=())
    household.project_cost = lambda node_id: project_cost
    household.funding_capacity = lambda: funding_capacity
    household.committed_spend = lambda: committed_spend
    # the project-start phase alone, unless the whole year is the thing being checked
    household.step() if whole_year else household._step_start_projects()
    return household


_room_clears = _start_room(funding_capacity=10000.0, committed_spend=0.0)
_room_short_on_capacity = _start_room(funding_capacity=8000.0, committed_spend=0.0)
_room_short_on_committed = _start_room(funding_capacity=1e7, committed_spend=1e7 - 5000.0)
check("scenario: a household whose funding_capacity() less committed_spend() clears every candidate's pinned cost starts "
      "new work; with funding_capacity() trimmed just below it, or committed_spend() eating almost all of a huge capacity, "
      "it starts nothing",
      len(_room_clears.active) > 0 and len(_room_short_on_capacity.active) == 0 and len(_room_short_on_committed.active) == 0,
      (list(_room_clears.active), list(_room_short_on_capacity.active), list(_room_short_on_committed.active)))
