"""Eminence and prominence (withdraw_from_public_life, the eminence
report's chance-of-ruin split) and the separate scandal/denouncement risk.

Regrouped from test_round8_fixes.py and test_round9.py - see CLAUDE.md's
test-file reorganisation note. Checks moved verbatim; each one's own comment
explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


def _big(rep=98.0, em=39.0, yr=250, cap=5000000.0):
    big_sim = sim(capital=cap)
    big_sim.done.update(list(NODES)[:1400]); big_sim._done_changed()
    big_sim.reputation, big_sim.eminence, big_sim.year = rep, em, yr
    return big_sim

_em = _big()
_rep0, _em0 = _em.reputation, _em.eminence
_ok_w, _why_w = _em.withdraw_from_public_life()
check("there is a command that lowers prominence the year you use it",
      _ok_w and _em.eminence < _em0 * 0.6, (_em0, _em.eminence))
check("...and its price is reputation, not money",
      _em.reputation < _rep0 - 5 and abs(_em.capital - 5000000.0) < 1e-6,
      (_rep0, _em.reputation, _em.capital))
check("...but never below what the work you built is worth on its own",
      _em.reputation >= _em.standing_floor() - 1e-6,
      (_em.reputation, _em.standing_floor()))
check("...and it cannot be done twice in a decade",
      _em.withdraw_from_public_life()[0] is False,
      _em.withdraw_from_public_life()[1])
_em2 = _big()
_em2.year += _em2.WITHDRAW_EVERY + 1
check("...and can be done again once enough years have passed",
      _em2.withdraw_from_public_life()[0], _em2.year)

# It must not take the price when there is nothing to buy - the same rule
# `bribe` learned the hard way.
_quiet = _big(rep=40.0, em=1.0)
_rq = _quiet.reputation
check("withdrawing when nobody is watching is refused, not charged",
      _quiet.withdraw_from_public_life()[0] is False
      and _quiet.reputation == _rq,
      (_quiet.reputation, _rq))

# The settling point was ABOVE the danger line, which is a promise that a
# successful run dies. Familiarity - the model's own measure of how
# unsurprising you have become - now damps it.
_fam = _big()
_fam.familiarity = 0.0
_cold = _fam.prominence_hazard()
_fam.familiarity = 0.9
_warm = _fam.prominence_hazard()
check("a city that has watched you for a century is less alarmed by you",
      _warm < _cold * 0.92, (_cold, _warm))
# A sixth off, not a third: the first attempt at this damping took the hazard
# so far down that a break tester measured three thousand run-years with the
# sum of every reported chance of ruin at exactly 0.00.
check("...but never stops being alarmed altogether",
      _warm > _cold * 0.8, (_cold, _warm))
# The shape that matters: build the counter and you sit under the line;
# do not and you sit well over it.
_em_shape = {}
for _acad in (False, True):
    _s = sim(capital=50000000.0)
    _s.done.update(list(NODES)[:1400])
    run_it(_s, "patron_imperial", "academy_network")
    if not _acad:
        _s.done.discard("academy_network")
        _s.operating.discard("academy_network")
    _s._done_changed()
    _s.reputation, _s.year, _s.familiarity = 98.0, 400, 0.9
    _em_shape[_acad] = _s.eminence_report()["settles_at_if_nothing_changes"]
check("a great man near the throne who built no academies is over the line",
      _em_shape[False] > sim().cfg["eminence_danger"], _em_shape)
check("...and the same man who built them is under it",
      _em_shape[True] < sim().cfg["eminence_danger"], _em_shape)

# "7% chance of ruin" was the chance SOMETHING landed; four fifths of those
# are survivable. A play tester survived two and was ended by the third.
_rep = _big().eminence_report()
check("the report separates 'something happens' from 'the run ends'",
      _rep["chance_the_run_ENDS_this_year"] < _rep["chance_of_ruin_this_year"],
      (_rep["chance_of_ruin_this_year"], _rep["chance_the_run_ENDS_this_year"]))
check("...and says which outcomes there are and how likely each is",
      abs(sum(_rep["if_it_lands_it_is"].values()) - 1.0) < 1e-9,
      _rep["if_it_lands_it_is"])
check("...and names the lever, by the word you would type",
      "withdraw" in str(_rep["the_one_lever"]), _rep["the_one_lever"])

# It has to survive a save, or a --session game gets a free retirement a year.
_wsv = "_withdrawtest.json"
_wsvp = os.path.join(ROOT, _wsv)
if os.path.exists(_wsvp):
    os.remove(_wsvp)
_rw, _, _ = proto([{"cmd": "withdraw"}, {"cmd": "save", "file": _wsv},
                   {"cmd": "load", "file": _wsv}, {"cmd": "withdraw"}])
check("a retirement cannot be repeated by saving and reloading",
      _rw[-1].get("ok") is False, _rw[-1])
if os.path.exists(_wsvp):
    os.remove(_wsvp)

# --- BREAK: "RUN ENDS: denounced: as a sorcerer" after eleven quiet years,
# with `state` showing "scandal 33.55" and no threshold and no probability -
# on the same screen where eminence explains itself in full.
s_sc = sim(events=True)
s_sc.scandal = 30.0
s_sc.year = 150
s_sc._said_scandal = 0
_st_sc = S._agent_state(s_sc, NODES)
check("state says what scandal is dangerous above",
      _st_sc.get("scandal_danger") is not None, _st_sc.get("scandal_danger"))
check("...and what the chance of being denounced this year is",
      _st_sc.get("chance_of_being_denounced_this_year", 0) > 0,
      _st_sc.get("chance_of_being_denounced_this_year"))
check("...and the page prints both, next to the eminence line that already did",
      "SCANDAL is dangerous above" in _RP("state", _st_sc),
      [line for line in _RP("state", _st_sc).splitlines() if "dangerous above" in line])
