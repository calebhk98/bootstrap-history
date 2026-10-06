"""Numbers that have to agree because a player reads them side by
side: `ventures` against the `money` ledger, `labour`'s wage bill against
the per-head quote, `work`'s three figures, three different screens'
counts of the founder's own staff, and `why`'s FULL CHAIN total against the
sum of what each node behind it would actually cost.

Regrouped from test_round8_fixes.py, test_round9.py and test_round10.py -
see CLAUDE.md's test-file reorganisation note (round 8f's own banner was
"screens that disagreed with each other" - the same theme, named by the
original author). Checks moved verbatim; each one's own comment explains
the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: "(these add up to the revenue above)" - 166.7 + 66.7 = 233.4
# under a stated 233.5. A claim of exact addition, checkable in one line.
for _civ_name in ("rome_100ad", "han_china_100ad"):
    _s = sim(civ=_civ_name, capital=200000.0)
    for _i, _k in enumerate(node_id for node_id in NODES if NODES[node_id]["rev"] > 0):
        if _i >= 6:
            break
        _s.done.add(_k); _s.operating.add(_k)
    _s._done_changed()
    _src = _s.revenue_sources()
    _sum = sum(value for value in _src.values() if isinstance(value, (int, float)))
    check("%s: the ledger rows add up to the revenue they are printed under"
          % _civ_name, abs(_sum - _s.revenue()) < 0.05, (_sum, _s.revenue()))

# --- BREAK: "market can supply 22,500 hours", then 24,500 after hiring one
# smith. market_supply is hours available TO YOU, your own staff included.
s_ms = sim(capital=200000.0)
_town0, _mine0 = s_ms.labour.market_supply_split("smith")
s_ms.labour.hire("smith", 1)
_town1, _mine1 = s_ms.labour.market_supply_split("smith")
check("hiring does not conjure more of a trade into the town",
      abs(_town0 - _town1) < 1e-6, (_town0, _town1))
check("...and what your own people add is counted separately",
      _mine1 > _mine0 and abs(_town1 + _mine1 - s_ms.labour.market_supply("smith")) < 1e-6,
      (_mine0, _mine1, s_ms.labour.market_supply("smith")))

# --- BREAK: after `hire smith 1`, `labour` dropped smith from YOU COULD HIRE,
# which reads as "no more smiths available" - and `hire smith 1` still worked.
def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


_game_a = sim()
_ask(_game_a, cmd="hire", trade="smith", n=1)
_rl = _ask(_game_a, cmd="labour")
check("a trade you employ is still listed as one you could hire",
      "smith" in (_rl.get("you_could_hire_here") or []),
      _rl.get("you_could_hire_here"))

# --- BREAK: F34, "numbers that do not reconcile, collected". Every one of
# these was a subtraction a break tester did on figures printed together.
_game_b = sim(capital=5.0e7)
_game_b.end_year = _game_b.cfg["start_year"] + _game_b.cfg["horizon_years"]
_ask(_game_b, cmd="hire", trade="smith", n=2)
_lab = _ask(_game_b, cmd="labour")
_wk = _ask(_game_b, cmd="work", trade="scribe", hours=500)
_ask(_game_b, cmd="start", id="units_standards")
_ask(_game_b, cmd="step", years=1)
_mn = _ask(_game_b, cmd="money")
_rows = {record["trade"]: record for record in (_lab.get("on_your_staff") or [])}
if "smith" in _rows:
    check("the wage bill is the quoted wage times the number of people",
          abs(_rows["smith"]["a_year_of_one"] * _rows["smith"]["you_employ"]
              - _lab["annual_wage_bill"]) < 1.0,
          (_rows["smith"], _lab["annual_wage_bill"]))
check("work's three figures subtract to each other",
      abs((_wk["earned"] - _wk["it_cost_your_own_practice"])
          - _wk["so_you_are_up"]) < 0.051, _wk)
check("money's net before and after the work in hand differ by exactly that",
      abs((_mn["net_per_year"] - _mn["spent_on_projects_last_year"])
          - _mn["net_after_project_spend"]) < 0.11, _mn)
_st2 = _ask(_game_b, cmd="state")
check("...and the after figure is the one `state` prints, to the decimal",
      "net_after_project_spend" in _st2, list(_st2)[:5])

# --- BREAK: `why med_cataract_couching` said "REVENUE: 500 den/yr" beside a
# ledger crediting 166.7 for the same node - `why` overstating income
# threefold, as a break tester put it.
_game_c = sim()
_rwy = [_ask(_game_c, cmd="why", id="med_cataract_couching")]
check("why says what a practice node pays YOU, not only what the trade is worth",
      _rwy[0].get("but_it_pays_YOU") is not None
      and _rwy[0]["but_it_pays_YOU"] < _rwy[0]["revenue"],
      (_rwy[0].get("revenue"), _rwy[0].get("but_it_pays_YOU")))
_st_r = [_ask(_game_c, cmd="money")]
_led = _st_r[0].get("where_the_money_comes_from") or {}
check("...and that figure is the ledger's, to the decimal",
      abs(_rwy[0]["but_it_pays_YOU"]
          - _led.get("med_cataract_couching", -1)) < 0.05 * len(_led) + 0.06,
      (_rwy[0].get("but_it_pays_YOU"), sorted(_led)[:4]))
_rwy2 = [_ask(_game_c, cmd="why", id="horse_collar")]
check("...and a node that is NOT your practice carries no such line",
      _rwy2[0].get("but_it_pays_YOU") is None, _rwy2[0].get("but_it_pays_YOU"))

# --- BREAK: `ventures` "1 scholars, 1 craftsmen" on the same screen as
# `labour`'s "ON YOUR STAFF: nobody". Three screens, three counts.
_rv2 = [_ask(_game_c, cmd="ventures"), _ask(_game_c, cmd="labour")]
check("the free-hands count says that one of them is you",
      _rv2[0].get("one_of_each_of_those_is_you") is True
      and _rv2[1].get("you_employ_in_total") == 0,
      (_rv2[0].get("people_free_to_run_something_new"),
       _rv2[1].get("you_employ_in_total")))

# --- BREAK: `ventures` understated every concern by a uniform 2.234x against
# the `money` ledger, and its NEEDS column printed the BUILD crew where the
# engine charges supervision - a quarter of it, and never the number the
# refusal quotes.
s_vv = sim(capital=5000000.0)
s_vv.done.update(NODES); s_vv._done_changed()
s_vv.artisans = s_vv.scholars = 40.0
_opened = 0
for _k in sorted(NODES):
    if s_vv.is_venture(_k) and _opened < 3 and s_vv.open_venture(_k)[0]:
        _opened += 1
for _ in range(1):
    s_vv.step()
_vr = S._agent_dispatch(s_vv, NODES, {"cmd": "ventures"})
_led = s_vv.revenue_sources()
check("ventures quotes the same earnings the ledger credits",
      bool(_vr["running"]) and all(abs(venture_row["earns_a_year"] - _led.get(venture_row["id"], venture_row["earns_a_year"])) < 0.11
          for venture_row in _vr["running"]),
      [(venture_row["id"], venture_row["earns_a_year"], _led.get(venture_row["id"])) for venture_row in _vr["running"]][:2])
check("...and its NEEDS column is the supervision the engine charges",
      all(abs(venture_row["needs"]["craftsmen"] - s_vv.venture_hands(venture_row["id"])[1]) < 0.011
          for venture_row in _vr["running"]),
      [(venture_row["id"], venture_row["needs"]) for venture_row in _vr["running"]][:2])

# --- BREAK: three places printed the founder's own staff differently. The
# prompt showed hired heads ("sch 0 art 0"), `why` compared a project against
# effective_scholars() and s.artisans ("you have 1, 0"), and start_project
# actually gated on craft_hands_available() - which counts the founder AND
# hours already bought. A play tester read two of the three on one turn and
# reported the game as having lost count of their household.
s_cn = sim(capital=20000.0)
_kn = next(node_id for node_id in sorted(NODES) if NODES[node_id]["art"] >= 2 and NODES[node_id]["sch"] == 0)
s_cn.labour.commission("mason", 4000.0)
_why_cn = S._node_explain(s_cn, NODES, _kn)
check("`why` counts the same artisans `start` does: yourself and hours bought",
      abs(_why_cn["you_have"]["artisans"] - round(s_cn.labour.craft_hands_available(), 1)) < 0.05,
      (_why_cn["you_have"], s_cn.labour.craft_hands_available(), s_cn.artisans))
check("...and says which people it is counting",
      "yourself" in str(_why_cn.get("you_have_counts")), _why_cn.get("you_have_counts"))
check("...and it is more than the bare payroll, having bought a mason's year",
      _why_cn["you_have"]["artisans"] > s_cn.artisans + 0.5,
      (_why_cn["you_have"]["artisans"], s_cn.artisans))
