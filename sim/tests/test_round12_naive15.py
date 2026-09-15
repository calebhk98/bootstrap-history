"""round12_naive15: split verbatim from the old test_regressions.py (original lines 12866-13075).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# ======================================================================
# ROUND 12: naive15 playtest, three findings.
# ======================================================================

# --- BREAK 1: a fully-built concern worth ~1,500/yr that could never be
# opened because the founder was short 0.01 of a craftsman's supervision
# time, and `mothball` - the tool for freeing committed resources - refused
# to release the tiny holder on the grounds it had no money upkeep, so
# there was "nothing to save". The resource actually short was staff time,
# not money, and mothball asked about money alone.
_s_mb = sim()
_mb_id = next(k for k, n in NODES.items()
              if n.get("up", 0) <= 0 and n.get("rev", 0) > 0 and _s_mb.is_venture(k))
_s_mb.done.add(_mb_id); _s_mb._done_changed()
_s_mb.operating.add(_mb_id)
_mb_sch, _mb_art = _s_mb.venture_hands(_mb_id)
check("the zero-upkeep venture used for this test really does tie up staff",
      _mb_art > 0.005 or _mb_sch > 0.005, (_mb_id, _mb_sch, _mb_art))
_mb_ok, _mb_msg = _s_mb.mothball_work(_mb_id)
check("mothball releases a concern whose cost is staff time, not money, "
      "even though its money upkeep is zero",
      _mb_ok, _mb_msg)
check("...and it actually frees the craftsmen/scholars it held, not just "
      "the (zero) money",
      _s_mb.venture_staff_used() == (0.0, 0.0), _s_mb.venture_staff_used())
check("...and says so, rather than only ever talking about money",
      "craftsm" in _mb_msg or "scholar" in _mb_msg, _mb_msg)
# A concern with genuinely nothing to save - no money upkeep, not running,
# so no staff held either - must still be refused honestly.
_s_mb2 = sim()
_mb2_id = next(k for k, n in NODES.items()
               if n.get("up", 0) <= 0 and n.get("rev", 0) <= 0
               and k not in _s_mb2.granted
               and not (_s_mb2.never_abandon(k) and n["cat"] in _s_mb2.NEVER_ABANDON))
_s_mb2.done.add(_mb2_id); _s_mb2._done_changed()
_mb2_ok, _mb2_msg = _s_mb2.mothball_work(_mb2_id)
check("...but a thing with genuinely nothing to save (no money, no staff "
      "held) is still refused, honestly",
      not _mb2_ok and "nothing to save" in _mb2_msg, _mb2_msg)

# --- BREAK 2a: `work <trade> <hours>` happily sells every founder-hour for
# wages, including the hours an active project still wants, with nothing
# said about it. A Norse playtester watched a project sit at "waiting on:
# your hours" for turns running because they kept selling all 2,000 hours a
# year, and asked for a warning, not a block - this is a legitimate way to
# raise cash.
_s_wk = sim(capital=500000.0)
_wk_id = next(k for k in NODES if NODES[k]["ph"] > 300 and NODES[k]["yrs"] >= 1)
_wk_n = NODES[_wk_id]
_s_wk.active[_wk_id] = dict(ph_left=float(_wk_n["ph"]), yrs=0.0, spent=0.0,
                            cost_left=100.0)
_wk_pay, _wk_err = _s_wk.work_for_wages("scholar", 2000)
check("selling every founder-hour is still allowed - this is not a block",
      _wk_pay > 0, _wk_pay)
check("...but it warns, naming the project and the hours it still wants",
      _wk_err and _wk_id in _wk_err and "hours" in _wk_err, _wk_err)
# The same sale with no active project at all draws no such warning.
_s_wk2 = sim(capital=500000.0)
_wk2_pay, _wk2_err = _s_wk2.work_for_wages("scholar", 2000)
check("...and says nothing about starving work when nothing is active",
      _wk2_err is None, _wk2_err)
# Selling only a few hours, leaving plenty for a SMALL-paced project, warns
# of nothing - this must not fire just because something, anything, is active.
_s_wk3 = sim(capital=500000.0)
_wk3_id = "sc2_notation_decimal_fraction"
_wk3_n = NODES[_wk3_id]
check("the small-paced project used for this test really is small-paced "
      "(under 100 hours a year), so the check below means something",
      _wk3_n["ph"] / max(1.0, _wk3_n["yrs"]) < 100, _wk3_n)
_s_wk3.active[_wk3_id] = dict(ph_left=float(_wk3_n["ph"]), yrs=0.0, spent=0.0,
                              cost_left=100.0)
_wk3_pay, _wk3_err = _s_wk3.work_for_wages("scholar", 10)
check("...and selling only a few idle hours does not warn either",
      _wk3_err is None, _wk3_err)

# --- BREAK 2b (Han): "waiting on: your hours" reported to persist after a
# project's hours were 100% spent and 0 still owed - a stale label, if the
# calendar floor was all that was left. Reproduced against the live
# _waiting_on (protocol.py): with founder-hours exhausted and nothing owed,
# it must name the calendar, not the founder's hours.
_s_cal = sim()
_cal_id = next(k for k in NODES if NODES[k]["yrs"] >= 2)
_cal_st = dict(ph_left=0.0, yrs=0.5, spent=100.0, cost_left=0.0)
_s_cal.active[_cal_id] = _cal_st
_cal_wo = _WO(_s_cal, NODES, _cal_id, _cal_st, 0.0)
check("a project with 100% of its hours spent and 0 still owed reports "
      "waiting on the calendar, not a stale 'your hours'",
      _cal_wo == "the calendar", _cal_wo)

# --- BREAK 3: `why`/`state` show only the single current blocker on an
# active project. A Han playtester fired a specialist whose hired-labour
# line read 0% owed, on the strength of `why` naming only "waiting on:
# money" - and the project broke immediately afterwards for a reason that
# had never been displayed. Root cause: core.py's stall detector asked
# whether a trade was EVER wanted by the node (n["lab"], a fixed total)
# rather than whether the project still owes that trade anything
# (lab_left) - the same question _waiting_on already answers correctly by
# reading lab_left, so the two disagreed. Once a project has drawn
# everything it will ever draw from a trade, losing that trade from the
# market must not be able to kill the project.
_s_eng = sim(capital=500000.0)
_eng_id = "ag2_cold_store"
check("ag2_cold_store really does need engineer hours, so this test means "
      "something", NODES[_eng_id]["lab"].get("engineer", 0) > 0, NODES[_eng_id]["lab"])
_s_eng.active[_eng_id] = dict(ph_left=50.0, yrs=0.0, spent=0.0, cost_left=100.0,
                              lab_left={"engineer": 0.0})
check("no engineers exist here, so the trade this project once needed is "
      "genuinely gone from the market",
      _s_eng.market_supply("engineer") <= 0.0, _s_eng.market_supply("engineer"))
_eng_log_before = len(_s_eng.log)
_s_eng.step()
check("a project that has already drawn everything it needed from a trade "
      "is not killed just because that trade later vanishes from the market",
      _eng_id in _s_eng.active
      and not any(_eng_id in m and "cannot go on" in m
                  for _, m in _s_eng.log[_eng_log_before:]),
      _s_eng.log[_eng_log_before:])
# The other half: a project that genuinely still owes a trade something is
# still correctly caught and warned before it is abandoned.
_s_eng2 = sim(capital=500000.0)
_s_eng2.active[_eng_id] = dict(ph_left=50.0, yrs=0.0, spent=0.0, cost_left=100.0,
                               lab_left={"engineer": 200.0})
_eng2_log_before = len(_s_eng2.log)
_s_eng2.step()
check("...while a project that genuinely still owes a trade something is "
      "still caught the first year it has nobody to do that work",
      any(_eng_id in m and "cannot go on" in m and "no engineer" in m
          for _, m in _s_eng2.log[_eng2_log_before:]),
      _s_eng2.log[_eng2_log_before:])

# And `why`/`state` were already telling the truth about the genuine case
# above (staffing_short reads lab_left, same as the fixed stall check now
# does) - the gap was only ever the disagreement between the two, not that
# _waiting_on itself was wrong.
_wo_eng = _WO(_s_eng2, NODES, _eng_id, _s_eng2.active[_eng_id],
             _s_eng2.active[_eng_id]["cost_left"])
check("...and `why`/`state` already named the real, still-owed shortfall "
      "before the fix, so the two now agree rather than one being taught "
      "to hide what the other one enforces",
      _wo_eng.startswith("nobody to do the work") and "engineer" in _wo_eng,
      _wo_eng)

# --- BREAK 3b: when a project is short on two DIFFERENT trades at once -
# one the society cannot supply at all, one only booked by the player's own
# other active work - _waiting_on used to report only the first and drop
# the second entirely, so a player deciding whether to fire someone could
# not see everything that decision would still leave broken.
_s_multi = sim(capital=500000.0)
_multi_id = next(k for k in NODES
                 if len(NODES[k].get("lab") or {}) >= 2 and NODES[k]["yrs"] >= 1)
_multi_trades = sorted((NODES[_multi_id]["lab"] or {}).keys())
_t_absent, _t_booked = _multi_trades[0], _multi_trades[1]
_multi_st = dict(ph_left=10.0, yrs=0.0, spent=0.0, cost_left=100.0,
                 lab_left=dict(NODES[_multi_id]["lab"]))
_s_multi.active[_multi_id] = _multi_st
# Force the market_supply of the "absent" trade to nothing, and pin the
# "booked" trade's own supply to something another active project consumes
# first, so one trade is a real absolute shortage and the other only a
# booking conflict.
_orig_market_supply = _s_multi.market_supply
def _fake_supply(t, _orig=_orig_market_supply, _absent=_t_absent):
    return 0.0 if t == _absent else _orig(t)
_s_multi.market_supply = _fake_supply
# Model a real portfolio-wide booking conflict.  _waiting_on deliberately uses
# this same aggregate as `portfolio`, rather than a stale consumed-hours tally.
_orig_trade_demand = _s_multi.trade_demand_vs_supply
def _fake_trade_demand(_orig=_orig_trade_demand, _booked=_t_booked):
    rows = _orig()
    rows.setdefault(_booked, {})["demand_hours_this_year"] = 10.0 ** 9
    return rows
_s_multi.trade_demand_vs_supply = _fake_trade_demand
_multi_wo = _WO(_s_multi, NODES, _multi_id, _multi_st, 100.0)
check("a project short on two different trades at once names both, not "
      "just the first one found",
      _t_absent in _multi_wo and _t_booked in _multi_wo, _multi_wo)
check("...and still leads with 'nobody to do the work', so 'portfolio' "
      "still classifies this the same way it always has",
      _multi_wo.startswith("nobody to do the work"), _multi_wo)

# THE MATERIAL BRAKE APPLIES TO WHAT THE FOUNDER ACTUALLY SPENDS, and a
# refactor that extracted step()'s hour formula into project_hour_pace folded
# self.throttle into the helper. That turns `min(remaining, want) * throttle`
# into `min(remaining, want * throttle)`, which is a different number whenever
# the founder's remaining hours are the binding term: remaining 100, want 500,
# throttle 0.5 gives 50 hours the old way and 100 the new. A busy year with
# the founder stretched thin is exactly when a material shortage should bite,
# and it silently stopped biting. Nothing in this suite caught it, so:
_s_th = sim()
_th_k = next(_k for _k in ORDER if _s_th.start_reason(_k)[0])
_s_th.start_project(_th_k)
_s_th.throttle = 0.5
_pace_half = _s_th.project_hour_pace(_th_k)
_s_th.throttle = 1.0
_pace_full = _s_th.project_hour_pace(_th_k)
check("project_hour_pace reports what a project WANTS, with no material "
      "brake folded in, because its callers apply the brake themselves and "
      "min(remaining, want) * throttle is not min(remaining, want * throttle)",
      abs(_pace_half - _pace_full) < 1e-9 and _pace_full > 0,
      (_pace_half, _pace_full))
check("...and the two orderings really do differ where it matters, so that "
      "check is guarding something real rather than restating an identity",
      abs(min(100.0, 500.0) * 0.5 - min(100.0, 500.0 * 0.5)) > 1e-9,
      (min(100.0, 500.0) * 0.5, min(100.0, 500.0 * 0.5)))

# NO BEHAVIOURAL CHECK OF THE BRAKE ITSELF HERE, deliberately, and this is
# the honest reason: step() recomputes self.throttle from the year's material
# supply at the top of every year, so a test that sets self.throttle and then
# calls step() is testing nothing at all - it measured 900.0 hours spent both
# with and without a shortage, because the value it set had already been
# overwritten before the line under test ever read it. Driving a real
# shortage far enough to move the throttle is a fixture this check does not
# have. The two checks above pin the actual regression, which is the helper
# folding the brake in, and the composed expression is a single line in
# core.py's step(). A check that cannot fail is worse than no check, because
# it reads like cover.

