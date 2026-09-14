"""arrears_hours: split verbatim from the old test_regressions.py (original lines 9851-9949).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# BREAK, REPORTED INDEPENDENTLY ON THREE CIVILISATIONS: "in arrears freezes
# ALL founder-hour progress even on fully-paid projects." Confirmed exactly:
# step()'s hour-allocation guarded the year's money draw with `if money >
# purse`, where `purse` is the household's own affordability (capital plus
# part of credit, less fixed costs) - but a project whose cost_left is
# already 0 asks for money=0 this YEAR, and 0 > purse is still true whenever
# the HOUSEHOLD'S purse has gone negative, nothing to do with this project's
# own bill. That forced funded_frac to 0.0 and refunded nearly the whole
# year's hours on a project that needed not one more denarius - a pure
# calendar wait turned into no progress at all, for as long as the
# household stayed in arrears, however long that ran.
# =============================================================================
s_af = sim(capital=1000.0)
_af_k = next(kk for kk in NODES if NODES[kk]["yrs"] >= 3 and NODES[kk]["ph"] > 500)
_af_n = NODES[_af_k]
# Injected directly into `active`, bypassing prerequisite legality, to
# isolate step()'s hour-allocation arithmetic from whether this particular
# node could be started today - the bug is in the allocation, not the gate.
s_af.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0,
                          spent=s_af.project_cost(_af_k), cost_left=0.0,
                          lab_left=dict(_af_n["lab"]))
_lim_af = s_af.credit_limit()
_fixed_af = s_af.living_cost() + s_af.upkeep() + s_af.mine_operating_cost()
_reserve_af = max(0.0, _fixed_af - s_af.revenue())
# Mildly in arrears - well clear of credit_limit (so enforce_credit_limit
# does not wipe `active` out from under this check), but still enough for
# THIS PROJECT's own purse (capital + 0.6*limit - reserve) to be negative.
s_af.capital = -(_reserve_af + 0.6 * _lim_af) - 50.0
check("set-up: in arrears, but nowhere near the credit limit itself, with "
      "a project that owes nothing further",
      s_af.capital > -_lim_af
      and s_af.active[_af_k]["cost_left"] == 0.0, s_af.capital)
_ph_before_af = s_af.active[_af_k]["ph_left"]
s_af.step()
check("a fully-paid project still makes real hour progress while the "
      "household is in arrears, rather than being refunded almost "
      "everything it was offered for a shortfall that is not its own",
      _af_k in s_af.active
      and s_af.active[_af_k]["ph_left"] < _ph_before_af - 100,
      (_ph_before_af, s_af.active.get(_af_k, {}).get("ph_left")))
check("...and it is not marked underfunded, because nothing was actually "
      "short - there was nothing left to pay for",
      not s_af.active.get(_af_k, {}).get("underfunded_this_year"),
      s_af.active.get(_af_k, {}).get("why_underfunded"))

# SPLIT-SUITE NOTE (not a content change, see this split's own report): the
# original monolithic file left `_k` bound to "cementation_steel" from the
# labour_productivity section, ~150 lines and one topic module earlier
# (test_labour_productivity.py's own reopen_restaffed_ventures check). This
# check does not care which venture node it is, only that it is one an
# artisan can staff; reproduced verbatim rather than silently fixed.
_k = "cementation_steel"

# --- and a concern a player shut ON PURPOSE must never reappear on its own -
# reopen_restaffed_ventures only undoes close_unstaffed_ventures, never `mothball`
s = sim(capital=50000.0)
s.done.add(_k)
s._done_changed()
s.employees["artisan"] = 6.0
s._resync_pools()
s.open_venture(_k)
s.mothball_work(_k)
reopened = s.reopen_restaffed_ventures(s.year)
check("a concern closed on purpose with 'mothball' is never auto-reopened, "
      "however much staff is free - that is still the player's call",
      reopened == [] and _k in s.mothballed and _k not in s.operating, reopened)

# --- the treadmill itself, measured: build a realistic spread of concerns,
# starve them of any staff replacement (auto_hire off, the player default),
# and count closures against automatic reopenings over 40 years
def _portfolio_run(auto_hire, years=40):
    s = sim(civ="norse_900ad", capital=60000.0)
    s.policy["auto_hire"] = auto_hire
    cands = sorted((k for k in NODES if s.is_venture(k) and NODES[k]["rev"] > 0),
                   key=lambda k: -(NODES[k]["rev"] / max(1.0, sum(s.venture_hands(k)))))
    chosen, need_sch, need_art = [], 0.0, 0.0
    for k in cands:
        s.done.add(k)
        a, b = s.venture_hands(k)
        if (need_sch + a > 8.0 and need_sch > 0) or (need_art + b > 35.0 and need_art > 0):
            s.done.discard(k)
            continue
        need_sch += a
        need_art += b
        chosen.append(k)
        if len(chosen) >= 25:
            break
    s._done_changed()
    s.employees["scholar"] = round(need_sch) + 1
    s.employees["artisan"] = round(need_art) + 2
    s._resync_pools()
    opened = [k for k in chosen if s.open_venture(k)[0]]
    reopenings = 0
    for _ in range(years):
        before = set(s.operating)
        s.step()
        reopenings += len((set(s.operating) - before) & set(opened))
    return opened, sum(1 for k in opened if k in s.operating), reopenings

_opened, _open_end, _reopenings = _portfolio_run(auto_hire=True)
check("with auto_hire replacing attrition losses, the portfolio it built "
      "fully recovers over 40 years - every closure eventually comes back "
      "on its own once the household can staff it again",
      _open_end == len(_opened) and _reopenings > 0,
      "opened %d, open at year 40: %d, auto-reopenings: %d"
      % (len(_opened), _open_end, _reopenings))
