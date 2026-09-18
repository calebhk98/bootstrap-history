"""affordability_warning: split verbatim from the old test_regressions.py (original lines 13076-13173).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
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
import inspect as _insp3
# STEP() PLUS ITS OWN PHASES, NOT step() ALONE. This read `getsource(Sim.step)`
# while step() was a single 1,760-line method and every phase of the year was
# inside it. step() is now a short sequence of `_step_*` phase methods, so the
# gate this check is about lives in `_step_start_projects` rather than in
# step()'s own body, and reading only step() fails this check by finding
# nothing, which says the phases moved rather than that the gate went private.
# The property being asserted has
# not changed: whichever phase runs the director's start heuristic must reach
# for the shared helpers rather than re-derive the same arithmetic privately.
# Gathering the phases by prefix keeps that true across any future re-split.
_step_src = "".join(
    [_insp3.getsource(S.Sim.step)]
    + [_insp3.getsource(getattr(S.Sim, name)) for name in sorted(dir(S.Sim))
       if name.startswith("_step_") and callable(getattr(S.Sim, name, None))])
check("step()'s own affordability gate calls the shared funding_capacity() "
      "and committed_spend(), not a second inline formula",
      "self.funding_capacity()" in _step_src and "self.committed_spend()" in _step_src,
      "checked step() and its _step_* phase methods")

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
