"""SCENARIO: eminence and prominence (withdraw_from_public_life, the eminence
report's chance-of-ruin split) and the separate scandal/denouncement risk, through a real game. The rules (when withdrawing is
refused, how far it lowers prominence, the hazard's familiarity relief, the ruin chances) are in
test_eminence_scandal_and_reputation.

Regrouped from test_round8_fixes.py and test_round9.py - see CLAUDE.md's
test-file reorganisation note. Checks moved verbatim; each one's own comment
explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


def _big(rep=98.0, eminence=39.0, year=250, cap=5000000.0):
    big_sim = unopened_sim(capital=cap)
    big_sim.done.update(list(NODES)[:1400]); big_sim._done_changed()
    big_sim.reputation, big_sim.eminence, big_sim.year = rep, eminence, year
    return big_sim

_em = _big()
_rep0, _em0, _cash0 = _em.reputation, _em.eminence, _em.capital
_ok_w, _why_w = _em.withdraw_from_public_life()
# (how far it lowers prominence and the floor under reputation: test_eminence_scandal_and_reputation)
check("the command withdraws, and its price is reputation, not money",
      _ok_w and _em.reputation < _rep0 and abs(_em.capital - _cash0) < 1e-6,
      (_rep0, _em.reputation, _em.capital, _cash0))

# The settling point was ABOVE the danger line, which is a promise that a
# successful run dies. Familiarity - the model's own measure of how
# unsurprising you have become - now damps it.
# The shape that matters: build the counter and you sit under the line;
# do not and you sit well over it.
_em_shape = {}
for _acad in (False, True):
    _s = unopened_sim(capital=50000000.0)
    _s.done.update(list(NODES)[:1400])
    run_it(_s, "patron_imperial", "academy_network")
    if not _acad:
        _s.done.discard("academy_network")
        _s.operating.discard("academy_network")
    _s._done_changed()
    _s.reputation, _s.year, _s.familiarity = 98.0, 400, 0.9
    _em_shape[_acad] = _s.eminence_report()["settles_at_if_nothing_changes"]
check("a great man near the throne who built no academies is over the line",
      _em_shape[False] > unopened_sim().cfg["eminence_danger"], _em_shape)
check("...and the same man who built them is under it",
      _em_shape[True] < unopened_sim().cfg["eminence_danger"], _em_shape)

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
_retired = unopened_sim(capital=5000000.0)
_retired.done.update(list(NODES)[:1400]); _retired._done_changed()
_retired.reputation, _retired.eminence, _retired.year = 98.0, 39.0, 250
_wsv = "_withdrawtest.json"
_wsvp = os.path.join(ROOT, _wsv)
if os.path.exists(_wsvp):
    os.remove(_wsvp)
try:
    _first = S._agent_dispatch(_retired, NODES, {"cmd": "withdraw"})
    S._agent_dispatch(_retired, NODES, {"cmd": "save", "file": _wsv})
    S._agent_dispatch(_retired, NODES, {"cmd": "load", "file": _wsv})
    _again = S._agent_dispatch(_retired, NODES, {"cmd": "withdraw"})
finally:
    if os.path.exists(_wsvp):
        os.remove(_wsvp)
check("a retirement cannot be repeated by saving and reloading",
      _first.get("ok") is True and _again.get("ok") is False, (_first, _again))

# --- BREAK: "RUN ENDS: denounced: as a sorcerer" after eleven quiet years,
# with `state` showing "scandal 33.55" and no threshold and no probability -
# on the same screen where eminence explains itself in full.
s_sc = unopened_sim(events=True)
s_sc.scandal = 30.0
s_sc.year = 150
s_sc._said_scandal = 0
_st_sc = S._agent_state(s_sc, NODES)
check("state says what scandal is dangerous above",
      _st_sc.get("scandal_danger") is not None, _st_sc.get("scandal_danger"))
check("...and what the chance of being denounced this year is",
      _st_sc.get("chance_of_being_denounced_this_year", 0) > 0,
      _st_sc.get("chance_of_being_denounced_this_year"))

# The "visibly rich" line is an amount of labour, so it follows the coin: the
# same capital in labour hours is the same wealth term whatever the money is.
from sim.constants import REGISTRY as _REGISTRY
_wealth_sims = {}
for _civ_name in ("rome_100ad", "han_china_100ad"):
    _w = unopened_sim(civ=_civ_name)
    _w.reputation, _w.familiarity = 0.0, 0.0
    _wealth_sims[_civ_name] = _w
_rome_sim, _han_sim = _wealth_sims["rome_100ad"], _wealth_sims["han_china_100ad"]
_rome_mph = _rome_sim.labour.money_per_labour_hour()
_han_mph = _han_sim.labour.money_per_labour_hour()
# Same capital in labour hours, as a share of the hazard at saturated wealth
# (other civilisation-specific weights cancel in the ratio).
_hours = 1.0e6  # below the threshold in hours, so the term is not saturated
_wealth_share = {}
for _civ_name, _s in _wealth_sims.items():
    _s.capital = 1.0e6 * _hours * _s.labour.money_per_labour_hour()
    _saturated = _s.prominence_hazard()
    _s.capital = _hours * _s.labour.money_per_labour_hour()
    _wealth_share[_civ_name] = _s.prominence_hazard() / _saturated
_rome_fixed, _han_fixed = _wealth_share["rome_100ad"], _wealth_share["han_china_100ad"]
check("the two civilisations' coins differ, so the test means something",
      abs(_rome_mph - _han_mph) > 1e-9 * max(_rome_mph, _han_mph), (_rome_mph, _han_mph))
check("the wealth term of the prominence hazard is the same at the same capital in labour hours",
      abs(_rome_fixed - _han_fixed) <= 1e-9 * max(_rome_fixed, _han_fixed, 1e-12)
      and _rome_fixed > 0.0, (_rome_fixed, _han_fixed))
# presentation: a declared unit string
check("the visibly-rich threshold is declared in labour hours",
      "labour hour" in _REGISTRY["EMINENCE_WEALTH_VISIBLE_THRESHOLD_LABOUR_HOURS"]["unit"])
