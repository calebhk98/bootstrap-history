"""Scenarios on a running game: a project the society cannot staff is stepped through its stall (the warning the first year, the
countdown in `state`, the crawl of one that is short of a trade but not of all) and finishes slowly instead of freezing; a stopped
project keeps its money and is billed the remainder when begun again, `why` quoting what `start` then charges; and selling hours for
wages warns about the project it starves. The rules (what a project waits on, the stall gate, `stop_project`, the cost block, the
warning, the hour pace) are in test_project_pacing."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of

# --- the stall, on a game stepped by years: the cold store (no engineer anywhere) and logarithms (more scribe-hours wanted than the
# society can field) are stepped together.
s_dl = sim(capital=20000000.0, surveyed=())
_need_eng = "ag2_cold_store"
s_dl.active[_need_eng] = dict(ph_left=float(NODES[_need_eng]["ph"]), yrs=0.0,
                              spent=0.0, cost_left=s_dl.project_cost(_need_eng))
for _p in NODES["logarithms"]["pre"]:
    s_dl.done.add(_p)
s_dl.scholars = s_dl.artisans = 50.0
for _cohort in ("children", "working_age", "elderly"):    # fewer people, so the trade is short of the project
    setattr(s_dl.population, _cohort, getattr(s_dl.population, _cohort) * 0.8)
s_dl._done_changed()
check("a project needing more of a trade than exists is startable",
      s_dl.start_project("logarithms")[0], s_dl.start_reason("logarithms"))
_dl_ph_left = [s_dl.active["logarithms"]["ph_left"]]
_dl_scribe_left = [s_dl.active["logarithms"]["lab_left"]["scribe"]]
s_dl._run_seat_work()    # the year's project work, without the economy around it
check("a project that cannot go on says so the first year, not the fourth",
      any(cause_of(message) == "project_cannot_go_on" and facts_of(message)["project"] == _need_eng for _, message in s_dl.log),
      [message for _, message in s_dl.log][:2])
_st_hl = S._agent_state(s_dl, NODES)["active"][_need_eng]
check("...and state carries the countdown and the trade that would save it",
      _st_hl.get("will_be_abandoned_in_years") == 3 and "engineer" in (_st_hl.get("because_nobody_here_can") or []), _st_hl)
if "logarithms" in s_dl.active:
    _dl_ph_left.append(s_dl.active["logarithms"]["ph_left"])
    _dl_scribe_left.append(s_dl.active["logarithms"]["lab_left"]["scribe"])
check("...and every year of the crawl really works down the hours and the scribe labour left",
      len(_dl_ph_left) == 2
      and all(later < earlier for earlier, later in zip(_dl_ph_left, _dl_ph_left[1:]))
      and all(later < earlier for earlier, later in zip(_dl_scribe_left, _dl_scribe_left[1:])),
      (_dl_ph_left, _dl_scribe_left))


def _logarithms_finishes_slowly():
    # The freeze was the end of the crawl, where the hours left are fewer than a year wants: put the
    # project at that tail, with a few hours, a little scribe labour and a small bill left, and the
    # calendar past its floor as the long crawl would have left it.
    s_dl.state.scenario.year = 101 + int(NODES["logarithms"]["yrs"])
    s_dl.active["logarithms"].update(ph_left=5.0, cost_left=5.0, yrs=float(NODES["logarithms"]["yrs"]))
    s_dl.active["logarithms"]["lab_left"]["scribe"] = 50.0
    for _ in range(2):
        if "logarithms" not in s_dl.active:
            break
        s_dl.step()
    finished = "logarithms" in s_dl.done
    return (finished and s_dl.done_year.get("logarithms", 0) - 100 > NODES["logarithms"]["yrs"],
            (s_dl.year, s_dl.active.get("logarithms"), s_dl.done_year.get("logarithms")))


slow_check("...and it finishes, slowly, longer than its calendar floor, instead of freezing for ever",
           _logarithms_finishes_slowly)

# --- stopping keeps the money, `why` quotes what starting again charges, and beginning again bills only the remainder
s_sp2 = sim(surveyed=())   # prices the project here
# a project startable now whose calendar floor outlasts one step, so it is still in hand after it
PACED = min((node_id for node_id in NODES if NODES[node_id]["yrs"] >= 2.0 and s_sp2.start_reason(node_id)[0]),
            key=lambda node_id: (s_sp2.project_cost(node_id), node_id))
s_sp = sim(capital=round(0.3 * s_sp2.project_cost(PACED)), surveyed=())   # part-payable at any wage scale
s_sp.start_project(PACED)
s_sp.step()
_spent_sp = s_sp.active[PACED]["spent"]
_ok_sp, _why_sp = s_sp.stop_project(PACED)
check("stopping a project keeps the money already paid",
      _ok_sp and abs(s_sp.paid_towards.get(PACED, 0.0) - _spent_sp) < 0.5, (s_sp.paid_towards, _spent_sp))
s_sp.capital = 50000.0
_sp_out = S._agent_dispatch(s_sp, NODES, {"cmd": "why", "id": PACED})
check("`why` on a halted, partly-paid project shows what 'start' would actually charge, the sunk amount accounting for the difference",
      abs(_sp_out["cost"]["already_paid_towards_this"] - _spent_sp) < 0.5
      and abs(_sp_out["cost"]["what_start_would_actually_charge"] - (_sp_out["cost"]["total"] - _spent_sp)) < 0.5, _sp_out["cost"])
_sp_start = S._agent_dispatch(s_sp, NODES, {"cmd": "start", "id": PACED})
check("...and it matches what `start` then bills, not a second estimate of it",
      abs(_sp_out["cost"]["what_start_would_actually_charge"] - _sp_start["the_bill_you_have_taken_on"]) < 0.5,
      (_sp_out["cost"]["what_start_would_actually_charge"], _sp_start.get("the_bill_you_have_taken_on")))
check("...and beginning again bills only the remainder",
      abs(s_sp.active[PACED]["cost_left"] - (s_sp.project_cost(PACED) - _spent_sp)) < 0.5, s_sp.active[PACED]["cost_left"])
check("...but the hours really are gone: that was your year",
      abs(s_sp.active[PACED]["ph_left"] - NODES[PACED]["ph"]) < 1e-6, s_sp.active[PACED]["ph_left"])
s_sp2.paid_towards = {PACED: s_sp2.project_cost(PACED) - 5.0}
check("...and a nearly-paid project is not refused for its gross price", s_sp2.start_project(PACED)[0], s_sp2.start_reason(PACED))

# --- selling every founder-hour is allowed but warns, naming the project it starves
_s_wk = unopened_sim(capital=500000.0)
_wk_id = next(node_id for node_id in NODES if NODES[node_id]["ph"] > 300 and NODES[node_id]["yrs"] >= 1)
_s_wk.active[_wk_id] = dict(ph_left=float(NODES[_wk_id]["ph"]), yrs=0.0, spent=0.0, cost_left=100.0)
_wk_pay, _wk_err = _s_wk.labour.work_for_wages("scholar", 2000)
check("selling every founder-hour is still allowed - this is not a block", _wk_pay > 0, _wk_pay)
check("...but it warns, naming the project it starves", bool(_wk_err) and _wk_id in _wk_err, _wk_err)
_s_wk2 = unopened_sim(capital=500000.0)
_wk2_pay, _wk2_err = _s_wk2.labour.work_for_wages("scholar", 2000)
check("...and says nothing about starving work when nothing is active", not _wk2_err, _wk2_err)
