"""market_saturation: split verbatim from the old test_regressions.py (original lines 10015-10076).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# MARKET SATURATION: A PENALTY THAT ATE HALF THE REVENUE AND WAS EXPLAINED
# NOWHERE A PLAYER WOULD READ IT BEFORE THE FACT. Two playtesters (Han,
# England) each watched a large, unexplained share of gross revenue vanish
# into goods_market_factor() - a real, intended mechanism (see COMMODITIES.md
# and GOODS_CATEGORIES) that simply had no total attached anywhere a player
# would read, and told a player nothing about a SECOND concern's earnings
# until after they had already opened it.
# =============================================================================
_ms1, _ms1_ids = _mk_loom_sim(1, 60)          # one mature loom
_k1 = _ms1_ids[0]
_k2 = next(k for k in sorted(NODES)
          if NODES[k].get("cat") == "textiles" and NODES[k].get("rev")
          and k != _k1)
_predicted = _ms1.goods_market_factor_if_opened(_k2)
check("goods_market_factor_if_opened predicts a SECOND concern's day-one "
      "factor before it is opened, rather than the flat 1.0 every screen "
      "listing a not-yet-open venture currently shows",
      _predicted < 0.9, _predicted)
_ms1.done.add(_k2)
_ms1.done_year[_k2] = _ms1.year
_ms1._done_changed()
for _trade, _required in NODES[_k2].get("lab", {}).get("trades", {}).items():
    _ms1.employees[_trade] = max(_ms1.employees.get(_trade, 0.0),
                                 float(_required))
_ms1.employees["master"] = max(_ms1.employees.get("master", 0.0), 1.0)
_opened_k2, _open_msg_k2 = _ms1.open_venture(_k2)
check("set-up: the second concern opens with its required specialist staff",
      _opened_k2, _open_msg_k2)
_actual = _ms1.goods_market_factor(_k2)
check("...matching what that concern would actually earn the instant it "
      "opened, not a different, invented number",
      abs(_predicted - _actual) < 1e-6, (_predicted, _actual))
_note_before = _mk_loom_sim(1, 60)[0].goods_market_note(_k2)
check("...and a player reading `ventures`/`why` about the SECOND concern "
      "before opening it is told so in words, naming market saturation by "
      "that name, before committing capital rather than after",
      bool(_note_before) and "market saturation" in _note_before,
      _note_before)
check("...and points at the actual way out: a different goods category is "
      "not competing for the same buyers",
      "DIFFERENT goods category" in (_note_before or ""), _note_before)

# THE AGGREGATE TOTAL: not only which single row is worst, but how much
# altogether, and what share of these concerns' own quoted figures that is -
# the "47% of gross revenue" a player has to be able to read directly.
_ms10, _ms10_ids = _mk_loom_sim(4, 80)
_summary10 = _ms10.goods_market_summary()
check("goods_market_summary states the aggregate denarii lost to market "
      "saturation and what share of these concerns' own figures that is, "
      "not only the single worst row",
      bool(_summary10) and "market saturation is taking about" in _summary10
      and "%" in _summary10, _summary10)

# GOODS_CATEGORIES' OWN DOCUMENTED FLOORS explain a large fraction lost
# WITHOUT any compounding bug: a lone mature concern in an eta<1 category
# settles at floor**(1-eta) of its own day-one figure, exactly the number
# _goods_category_ratios computes, and two or more concerns in the SAME
# category divide that further by n_active - both are the documented,
# intended mechanism, not an accident stacking two effects on the same money.
for _cat, _cfg in S.Sim.GOODS_CATEGORIES.items():
    if _cfg["eta"] >= 1.0:
        continue
    _asym = _cfg["floor"] ** (1.0 - _cfg["eta"])
    check("%s's documented floor/eta gives the asymptote _goods_category_"
          "ratios actually computes for one lone, fully-saturated concern"
          % _cat,
          0.0 < _asym < 1.0, _asym)
