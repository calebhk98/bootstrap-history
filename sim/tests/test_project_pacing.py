"""Active projects (the `active` dict, not a running concern): pacing,
stalls, abandonment, stopping/restarting and the material throttle.

Regrouped from test_round8_fixes.py, test_round9.py, test_round10.py and
test_round12_naive15.py - see CLAUDE.md's test-file reorganisation note.
Checks moved verbatim; each one's own comment explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: "waiting on money" while holding 73,234,107 denarii against
# 45,448 owed. step() pays at most one year's instalment - the cost over the
# node's calendar floor - so a ten-year work absorbs a tenth a year however
# rich you are, and nothing anywhere said there was a pace at all.
from engine.protocol import _waiting_on as _WO
s_pace = sim(capital=50000000.0)
_slow = "academy_network"
s_pace.active[_slow] = dict(ph_left=0.0, yrs=1.0, spent=0.0,
                            cost_left=s_pace.project_cost(_slow))
_msg_rich = _WO(s_pace, NODES, _slow, s_pace.active[_slow],
                s_pace.active[_slow]["cost_left"])
check("a rich player is told the pace, not that they are short of money",
      "pace" in _msg_rich and "a year" in _msg_rich, _msg_rich)
check("...and is told how many more years that pace needs",
      "year" in _msg_rich and any(char.isdigit() for char in _msg_rich), _msg_rich)
s_broke = sim(capital=1.0)
s_broke.credit_limit = lambda: 0.0
s_broke.active[_slow] = dict(ph_left=0.0, yrs=1.0, spent=0.0,
                             cost_left=s_broke.project_cost(_slow))
_msg_poor = _WO(s_broke, NODES, _slow, s_broke.active[_slow],
                s_broke.active[_slow]["cost_left"])
check("...and a player who really cannot raise the instalment is told that",
      _msg_poor.startswith("money"), _msg_poor)

# --- BREAK: six projects wiped in one year. The countdown to abandonment ran
# silently for three years and then took everything spent.
s_hl = sim(capital=500000.0)
_need_eng = "ag2_cold_store"
s_hl.active[_need_eng] = dict(ph_left=float(NODES[_need_eng]["ph"]), yrs=0.0,
                              spent=0.0, cost_left=s_hl.project_cost(_need_eng))
s_hl.step()
check("a project that cannot go on says so the first year, not the fourth",
      any(_need_eng in message and "before it is abandoned" in message for _, message in s_hl.log),
      [message for _, message in s_hl.log][:2])
_st_all = S._agent_state(s_hl, NODES)
_st_hl = _st_all["active"][_need_eng]
check("...and state carries the countdown and the trade that would save it",
      _st_hl.get("will_be_abandoned_in_years") == 3
      and "engineer" in (_st_hl.get("because_nobody_here_can") or []),
      _st_hl)
check("...and the page says the one command that keeps your hours",
      "stop %s" % _need_eng in _RP("state", _st_all),
      [line for line in _RP("state", _st_all).splitlines() if "ABANDONED" in line])

# --- BREAK: a permanent deadlock. `logarithms` wants 10,000 scribe-hours a
# year where the society can field 8,750, so the throttle gives back a
# fraction of the work every year - and with no floor under the refund it gave
# back ALL of it. Founder-hours sat at exactly 5.0 for ever, the bill paid,
# the calendar long past, holding the whole scribe pool and freezing eight
# projects behind it - one of them scientific_method, a 230-denarius node
# startable in year 100 and still unbuilt at the horizon.
s_dl = sim(capital=20000000.0)
for _p in NODES["logarithms"]["pre"]:
    s_dl.done.add(_p)
s_dl.scholars = s_dl.artisans = 50.0
s_dl._done_changed()
check("a project needing more of a trade than exists is startable",
      s_dl.start_project("logarithms")[0], s_dl.start_reason("logarithms"))
for _ in range(60):
    s_dl.step()
    if "logarithms" not in s_dl.active:
        break
check("...and it finishes, slowly, instead of freezing for ever",
      "logarithms" in s_dl.done, (s_dl.year, s_dl.active.get("logarithms")))
check("...and it took longer than its calendar floor, because it crawled",
      s_dl.done_year.get("logarithms", 0) - 100 > NODES["logarithms"]["yrs"],
      s_dl.done_year.get("logarithms"))

# --- BREAK: `stop` burned the money as well as the hours, "same as a real
# abandoned enterprise" - so when the creditors were about to take everything,
# stopping something yourself cost exactly as much as letting them, and `stop`
# was never the right move. The site does not un-dig itself either way.
s_sp = sim()
s_sp.start_project("identity_cover")
for _ in range(2):
    s_sp.step()
_spent_sp = s_sp.active["identity_cover"]["spent"]
_ok_sp, _why_sp = s_sp.stop_project("identity_cover")
check("stopping a project keeps the money already paid",
      _ok_sp and abs(s_sp.paid_towards.get("identity_cover", 0.0)
                     - _spent_sp) < 0.5,
      (s_sp.paid_towards, _spent_sp))
check("...and says so",
      "comes off the bill" in str(_why_sp), _why_sp)
s_sp.capital = 50000.0
s_sp.start_project("identity_cover")
check("...and beginning again bills only the remainder",
      abs(s_sp.active["identity_cover"]["cost_left"]
          - (s_sp.project_cost("identity_cover") - _spent_sp)) < 0.5,
      s_sp.active["identity_cover"]["cost_left"])
check("...but the hours really are gone: that was your year",
      abs(s_sp.active["identity_cover"]["ph_left"]
          - NODES["identity_cover"]["ph"]) < 1e-6,
      s_sp.active["identity_cover"]["ph_left"])
# And the affordability gate has to test the REMAINDER, or a nearly-paid-for
# project is refused for a bill it no longer owes.
s_sp2 = sim()
s_sp2.paid_towards = {"identity_cover": s_sp2.project_cost("identity_cover") - 5.0}
check("...and a nearly-paid project is not refused for its gross price",
      s_sp2.start_project("identity_cover")[0],
      s_sp2.start_reason("identity_cover"))

# --- BREAK: `start` discounts a halted project's remaining bill by what was
# already sunk into it (see _paid_now above) - but `why` kept quoting the
# gross sticker price forever, for a project a creditor or the player's own
# `stop` had halted partway. An England player planning from `why` was
# planning against a number the engine would never actually charge; the
# real, discounted figure showed up only inside a `start` refusal or its
# success line, after the fact.
s_wp = sim(capital=1000.0)
_wp_k = next(node_id for node_id in s_wp.order if s_wp.can_start(node_id) and NODES[node_id]["ph"] > 0)
s_wp.start_project(_wp_k)
s_wp.active[_wp_k]["spent"] = 500.0
s_wp.stop_project(_wp_k)
_wp_out = S._agent_dispatch(s_wp, NODES, {"cmd": "why", "id": _wp_k})
check("`why` on a halted, partly-paid project shows both the gross total "
      "and what 'start' would actually charge, with the sunk amount "
      "accounting for the difference",
      _wp_out["cost"].get("already_paid_towards_this") == 500.0
      and abs(_wp_out["cost"]["what_start_would_actually_charge"]
              - (_wp_out["cost"]["total"] - 500.0)) < 0.5,
      _wp_out["cost"])
check("...and it matches what `start` would actually bill, not a second "
      "estimate of it",
      abs(_wp_out["cost"]["what_start_would_actually_charge"]
          - S._agent_dispatch(s_wp, NODES, {"cmd": "start", "id": _wp_k}
                              )["the_bill_you_have_taken_on"]) < 0.5,
      (_wp_out["cost"]["what_start_would_actually_charge"],))
# And the ordinary case - nothing sunk into this node - gets no such field.
s_wp2 = sim(capital=1000.0)
_wp2_k = next(node_id for node_id in s_wp2.order if s_wp2.can_start(node_id))
_wp2_out = S._agent_dispatch(s_wp2, NODES, {"cmd": "why", "id": _wp2_k})
check("...while a project with nothing sunk into it gets no discount "
      "field at all - there is nothing to discount",
      "already_paid_towards_this" not in _wp2_out["cost"], _wp2_out["cost"])

# --- BREAK 2a: `work <trade> <hours>` happily sells every founder-hour for
# wages, including the hours an active project still wants, with nothing
# said about it. A Norse playtester watched a project sit at "waiting on:
# your hours" for turns running because they kept selling all 2,000 hours a
# year, and asked for a warning, not a block - this is a legitimate way to
# raise cash.
_s_wk = sim(capital=500000.0)
_wk_id = next(node_id for node_id in NODES
              if NODES[node_id]["ph"] > 300 and NODES[node_id]["yrs"] >= 1)
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
_cal_id = next(node_id for node_id in NODES if NODES[node_id]["yrs"] >= 2)
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
      and not any(_eng_id in message and "cannot go on" in message
                  for _, message in _s_eng.log[_eng_log_before:]),
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
      any(_eng_id in message and "cannot go on" in message
          and "no engineer" in message
          for _, message in _s_eng2.log[_eng2_log_before:]),
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
_multi_id = next(node_id for node_id in NODES
                 if len(NODES[node_id].get("lab") or {}) >= 2 and NODES[node_id]["yrs"] >= 1)
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
def _fake_supply(trade, _orig=_orig_market_supply, _absent=_t_absent):
    return 0.0 if trade == _absent else _orig(trade)
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
_th_k = next(_node_id for _node_id in ORDER if _s_th.start_reason(_node_id)[0])
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
