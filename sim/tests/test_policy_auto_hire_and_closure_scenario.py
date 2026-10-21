"""Scenarios on running games: policies, creditors and the states a work can be in. The rules (what a review spares and closes, the payroll
a household lets go, the default policy, the stall diagnosis, the fee to reopen a work, a hazard's values delta) are in
test_policy_auto_hire_and_closure. Four named scenarios: a mothballed or forgotten work (start, available, restore, the invariants of
`operating` and `mothballed` against `done`), the start gates and a thin-surplus household, the year's hours, and a rich household's
first year under auto-hire. Each is a smoke test of wiring, not of one rule."""
import time as _time

from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of
from .agent_command_helpers import pristine_game

_LOSS = "md2_sand_filtration"

# ============================================================================
# Scenario 1: a mothballed or forgotten work
# ============================================================================
_pos = unopened_sim(capital=100000.0)
s = _pos
s.done.add(_LOSS); s._done_changed()      # you BUILT it; that is what mothballing means
s.mothballed.add(_LOSS)
ok, why = s.start_reason(_LOSS)
check("a mothballed work refuses to be started as if it were new research",
      not ok and s.start_blockers(_LOSS)[0]["cause"] == "mothballed", s.start_blockers(_LOSS))
avail = S._agent_available(s, NODES, {"all": True})
check("a mothballed work does not appear in available looking like new research",
      not any(entry["id"] == _LOSS for entry in avail["available"]), avail["count"])

# THE DEADLOCK. A play tester lost precision_three_plate to a sack and could not get it back by any verb: `start` sent them to
# `restore`, `restore` said they no longer knew how, `open` said they had not built it, `mothball` said there was nothing to shut.
_pos.done.discard(_LOSS)                  # known no longer, but still mothballed
_pos._done_changed()
s_dl = _pos
s_dl.trades_created.add("engineer")
s_dl.employees["engineer"] = 2.0
s_dl.mothballed.add(_LOSS)                # mothballed, and NOT known: the trap
ok_dl, why_dl = s_dl.start_reason(_LOSS)
check("a work whose knowledge was destroyed can be built again", ok_dl, why_dl)
ok_rs, why_rs = s_dl.restore_work(_LOSS)
check("...and restore says to build it, not that it cannot be restored", not ok_rs and "start" in why_rs, why_rs)
_av_dl = S._agent_available(s_dl, NODES, {"all": True})
check("...and it is visible in available, not hidden behind a stale mothball",
      any(entry["id"] == _LOSS for entry in _av_dl["available"]), _av_dl["count"])
s_dl.start_project(_LOSS)
check("...and starting it clears the stale mothball entry",
      _LOSS not in s_dl.mothballed and _LOSS in s_dl.active, (_LOSS in s_dl.mothballed, _LOSS in s_dl.active))

# Insolvency abandonment discarded from `done` AND added to `mothballed` (the pair of lines fixed twice elsewhere).
_neg = unopened_sim(capital=-100000.0)
_neg.state.founder.policy["auto_shed"] = True
s_ab = _neg
s_ab.done.add(_LOSS); s_ab._done_changed()
s_ab.operating.add(_LOSS)
s_ab.revenue = lambda: 0.0
s_ab._step_money_seat()    # the year's money phase is where insolvency sheds
check("no path in the engine leaves a work mothballed but unknown",
      _LOSS in s_ab.mothballed and not (s_ab.mothballed - s_ab.done), sorted(s_ab.mothballed - s_ab.done)[:4])
s_cr = unopened_sim(civ="norse_900ad", capital=-100000.0)
s_cr.done.add(_LOSS); s_cr._done_changed(); s_cr.operating.add(_LOSS)
s_cr.credit_limit = lambda: 0.0
s_cr.enforce_credit_limit(100)
check("creditors' seizure cannot leave you running what you no longer know",
      not sorted(s_cr.operating - s_cr.done), sorted(s_cr.operating - s_cr.done))

# Shutting a work down and reopening it is never free.
s_rt = unopened_sim(capital=50000.0)
run_it(s_rt, _LOSS, *NODES[_LOSS]["pre"])  # the work runs, and restore_work refuses while a prerequisite is shut
s_rt.mothball_work(_LOSS)
_cap = s_rt.capital
s_rt.restore_work(_LOSS)
check("shutting a work down and reopening it is never free",
      _cap - s_rt.capital >= NODES[_LOSS]["up"],
      "%s round trip cost %.0f against %.0f a year of upkeep" % (_LOSS, _cap - s_rt.capital, NODES[_LOSS]["up"]))

# ============================================================================
# Scenario 2: the start gates, and a household with a thin surplus
# ============================================================================
s = unopened_sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
s._step_staff()    # the year's staff phase is where auto_hire acts
check("auto_hire does not overcommit turn one against a thin surplus",
      s.scholars < 0.2 and s.artisans < 0.6, "scholars %.3f artisans %.3f capital %.1f" % (s.scholars, s.artisans, s.capital))

# Losing staff you cannot pay is written in the log, never silent.
s = sim(surveyed=())
s.capital = 22400.0 * s.labour.money_per_labour_hour()   # 22400 labour hours in coin
s.policy["auto_hire"] = False
s.labour.hire("smith", 5)
s.capital = -s.credit_limit() * 1.5
_b2 = sum(s.employees.values())
s._step_staff()
check("losing staff you cannot pay is written in the log, never silent",
      sum(s.employees.values()) < _b2 and any(cause_of(message) == "staff_left_unpaid" for _year, message in s.log),
      "%.2f -> %.2f, log %r" % (_b2, sum(s.employees.values()), s.log[-3:]))

# `start` is demand-led: a node startable but for the trade is accepted with ignore_trade, refused for the trade without it, and a
# trade being trained is a warning, not a refusal.
s = sim(civ="rome_100ad", capital=1e6, manual=True, events=False, surveyed=())
ok_ig, why_ig = s.start_reason("ag2_hydrometer", ignore_trade=True)
check("ignore_trade accepts a node that is startable but for the trade alone", ok_ig, why_ig)
ok_norm, why_norm = s.start_reason("ag2_hydrometer")
_blocker_norm = s.start_blockers("ag2_hydrometer")[0]
check("without ignore_trade the same node is refused specifically for the trade",
      not ok_norm and _blocker_norm["cause"] == "absent_trades"
      and "optician" in [trade for trade in NODES["ag2_hydrometer"]["lab"] if not s.labour.trade_available(trade)], _blocker_norm)
s.done.update(NODES["ag2_cold_store"]["pre"])  # prerequisites held, so only staffing can refuse
ok_staff, why_staff = s.start_reason("ag2_cold_store", ignore_trade=True)
check("ignore_trade still refuses a node blocked by missing STAFF, not just the trade",
      not ok_staff and s.start_blockers("ag2_cold_store")[0]["cause"] == "craft_staff", why_staff)
node = "ag2_cold_store"
s.artisans, s.scholars = 10.0, 10.0
r0 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start refuses outright when a needed trade has never been taught",
      not r0["ok"] and r0.get("blocked_cause") == "absent_trades"
      and "engineer" in [trade for trade in NODES[node]["lab"] if not s.labour.trade_available(trade)], r0)
s.labour.train("engineer", 2)          # training begun; nobody is ready for two years
r1 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start accepts work nobody can do yet only WITH a warning naming the trade",
      r1["ok"] and "engineer" in r1.get("warning", ""), r1)

# ============================================================================
# Scenario 3: where the founder's hours went in a year
# ============================================================================
ratios = []
# a project the society can staff, with the purse far short of its instalment, so the very first year shows a refund
s.start_project("scientific_method")
s.capital = -s.credit_limit() * 0.1
s._step_market = lambda: None   # the hours and the refund come from the work phases; the market close adds nothing to them
for _ in range(3):
    s.step()
    h = s.hours_this_year
    total = h["wage_work"] + h["teaching"] + h["offered_to_projects"] + h["unused"]
    check("a year's founder hours are fully accounted for (year %d)" % s.year, abs(total - h["available"]) < 1e-6, h)
    for k, pst in s.active.items():
        off = pst.get("hours_offered_this_year", 0.0)
        eff = pst.get("hours_effective_this_year", 0.0)
        if off > 1:
            ratios.append(eff / off)
    if any(abs(ratio - 0.5) > 0.02 for ratio in ratios):
        break     # the property is shown; further years only cost time
check("an underfunded project's refund is proportional, not always exactly half",
      any(abs(ratio - 0.5) > 0.02 for ratio in ratios), ratios)
st = S._agent_state(s, NODES, {})
check("state reports the year's hours summary", st.get("hours_this_year") == s.hours_this_year, st.get("hours_this_year"))
check("state reports hours offered/effective per active project",
      not st["active"] or any("hours_offered_this_year" in value for value in st["active"].values()), st["active"])

# ============================================================================
# Scenario 4: a rich household's first year under auto-hire, and `available` under fog
# ============================================================================
s = sim(civ="han_china_100ad", manual=False)
# Han's coin is small, so a fixed purse is a fraction of a labourer-year.
s.capital = 1000 * s.labour.market.quote_annual("labourer")
s.policy["auto_hire"] = True
run_it(s, _LOSS, *NODES[_LOSS]["pre"])   # a household with something running, so the invariant read below is not vacuous
s._step_market = lambda: None            # hiring and shedding act in the staff and money phases, not in the market close
s.step()
check("auto_hire on a rich household actually hires", sum(s.employees.values()) > 1.0, "staff %.2f on %.0f" % (sum(s.employees.values()), s.capital))
check("a long run never ends up running something it does not know",
      s.operating and not sorted(s.operating - s.done), sorted(s.operating - s.done)[:5])

# `available` must return quickly even deep in the tree under fog (start_reason recursing into is_visible, unmemoised, once took
# a single call on norse_900ad from instant to over a minute).
s = sim(civ="norse_900ad")
s.fog = True
s.revealed = set()
t0 = _time.time()
S._agent_available(s, NODES, {})
elapsed = _time.time() - t0
check("available returns quickly under fog, not in tens of seconds", elapsed < 5.0, "%.2fs" % elapsed)
