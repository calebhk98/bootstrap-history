"""affordability_warning: the aggregate affordability warning. Five naive playtests, five civilisations, and four of
them bankrupted themselves the same way: two or three "almost everything rests on this" foundations, each priced
correctly by `start`'s own "on_credit" forecast, started together on a poor scholar's opening capital. Nothing added
them up. committed_spend() and funding_capacity() are the one formula, and the warning `start` builds is from them.

The warning's rule (`stacked_commitment`) and the parts of the funding capacity (`funding_parts`) are tested on built
numbers; three named scenarios run the Rome opening through `start`, `money` and `available`, and the director's
project start gate."""
from .harness import *  # noqa: F401,F403

from sim.engine.project_funding import funding_parts
from sim.ui.proto.start_commitment import stacked_commitment

# --- the warning: only when several projects together owe more than the cash held
warned = stacked_commitment(644.0, 400.0, 2, lambda: 1500.0)
check("two projects owing more than the cash held are warned of, with the total, the cash and the draw on credit",
      warned == {"you_have_promised": 644.0, "across_projects_in_hand": 2, "you_currently_hold": 400.0,
                 "likely_to_draw_on_credit_between_them": 244.0, "your_real_ceiling_if_it_comes_to_that": 1500.0}, warned)
check("a single active project never gets the aggregate warning, however large: on_credit answers for it alone",
      stacked_commitment(5000.0, 400.0, 1, lambda: 1500.0) is None)
check("plenty of cash on hand: no aggregate warning even with several things started together",
      stacked_commitment(644.0, 1.0e6, 3, lambda: 1500.0) is None and stacked_commitment(644.0, 644.0, 3, lambda: 1.0) is None)
check("a household in arrears holds no cash, so what is owed is all drawn on credit",
      stacked_commitment(300.0, -50.0, 2, lambda: 10.0)["you_currently_hold"] == 0.0
      and stacked_commitment(300.0, -50.0, 2, lambda: 10.0)["likely_to_draw_on_credit_between_them"] == 300.0)
asked = []
stacked_commitment(100.0, 1000.0, 2, lambda: asked.append(1) or 5.0)
check("the ceiling is only worked out when there is a warning", asked == [])

# --- the funding capacity in parts: cash, the drawable credit, the surplus over the planning years
solvent = funding_parts(1000.0, 900.0, 600.0, 0.1, 400.0, 0.5, 5.0, 250.0)
check("cash held, half the credit line, and the planning years of the yearly surplus make up the funding capacity",
      solvent["cash_on_hand"] == 1000.0 and solvent["credit_available_now"] == 200.0
      and solvent["sustainable_annual_surplus"] == 300.0 and solvent["surplus_allowance_over_years"] == 1500.0
      and solvent["surplus_years_counted"] == 5.0 and solvent["already_committed"] == 250.0, solvent)
arrears = funding_parts(-100.0, 900.0, 600.0, 0.1, 400.0, 0.5, 5.0, 0.0)
check("arrears hold no cash, use up the room on the credit line, and their interest is a fixed cost that shrinks the surplus",
      arrears["cash_on_hand"] == 0.0 and arrears["credit_available_now"] == 100.0
      and abs(arrears["sustainable_annual_surplus"] - (900.0 - 610.0)) < 1e-9, arrears)
check("revenue short of fixed costs leaves no surplus, and arrears past the credit line leave no credit",
      funding_parts(1000.0, 500.0, 600.0, 0.1, 400.0, 0.5, 5.0, 0.0)["surplus_allowance_over_years"] == 0.0
      and funding_parts(-900.0, 0.0, 0.0, 0.1, 400.0, 0.5, 5.0, 0.0)["credit_available_now"] == 0.0)

# --- scenario: the Rome opening starts two foundations on a poor purse; `money` and `available` read the same numbers
s = sim(capital=400.0, surveyed=())
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
_probe = sim(surveyed=())
_sci_cost = _probe.project_cost("scientific_method")
_units_cost = _probe.project_cost("mt2_sintering_process")
_purse = round(_units_cost) - 44.0     # just short of the second project alone
s = sim(surveyed=())
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
    household = sim(capital=1e7, manual=False, surveyed=())
    household.project_cost = lambda node_id: project_cost
    household.funding_capacity = lambda: funding_capacity
    household.committed_spend = lambda: committed_spend
    # the project-start phase alone, unless the whole year is the thing being checked
    household.step() if whole_year else household._step_start_projects()
    return household


_room_clears = _start_room(funding_capacity=10000.0, committed_spend=0.0, whole_year=True)
_room_short_on_capacity = _start_room(funding_capacity=8000.0, committed_spend=0.0)
_room_short_on_committed = _start_room(funding_capacity=1e7, committed_spend=1e7 - 5000.0)
check("scenario: a household whose funding_capacity() less committed_spend() clears every candidate's pinned cost starts "
      "new work; with funding_capacity() trimmed just below it, or committed_spend() eating almost all of a huge capacity, "
      "it starts nothing",
      len(_room_clears.active) > 0 and len(_room_short_on_capacity.active) == 0 and len(_room_short_on_committed.active) == 0,
      (list(_room_clears.active), list(_room_short_on_capacity.active), list(_room_short_on_committed.active)))
