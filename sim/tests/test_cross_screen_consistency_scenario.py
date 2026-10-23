"""SMOKE: numbers that have to agree because a player reads them side by side: `work`'s figures, `money`'s two nets, `why` against the ledger and against `start`, and `ventures` against the ledger.
One unopened game per section, no year stepped. The ledger's rows adding up to the
revenue is test_training_ledger_and_hazard_reports; the town and own-staff split of a trade's hours is test_market_supply_split_rule.
"""
from .harness import *  # noqa: F401,F403


def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


# --- BREAK: F34, "numbers that do not reconcile, collected". Every one of
# these was a subtraction a break tester did on figures printed together.
_game_b = unopened_sim(capital=5.0e7)
_game_b.end_year = _game_b.cfg["start_year"] + _game_b.cfg["horizon_years"]
_ask(_game_b, cmd="hire", trade="smith", n=2)
_wk = _ask(_game_b, cmd="work", trade="scribe", hours=500)
_ask(_game_b, cmd="start", id="units_standards")
_mn = _ask(_game_b, cmd="money")
check("work reports the wage and no separate practice cost",
      _wk["earned"] > 0 and "it_cost_your_own_practice" not in _wk and "so_you_are_up" not in _wk, _wk)
_st2 = _ask(_game_b, cmd="state")
check("`money` and `state` print the same net after the work in hand",
      _mn["net_after_project_spend"] == _st2["net_after_project_spend"],
      (_mn["net_after_project_spend"], _st2.get("net_after_project_spend")))

# --- BREAK: `why med_cataract_couching` printed the trade's quoted revenue beside a ledger crediting
# the founder's job another figure. A held skill's line is the founder's one wage, the ledger's own row.
_game_c = unopened_sim()
_rwy = [_ask(_game_c, cmd="why", id="med_cataract_couching")]
check("why says what a held-skill node pays YOU",
      _rwy[0].get("but_it_pays_YOU") is not None and _rwy[0]["but_it_pays_YOU"] > 0.0,
      (_rwy[0].get("revenue"), _rwy[0].get("but_it_pays_YOU")))
_st_r = [_ask(_game_c, cmd="money")]
_led = _st_r[0].get("where_the_money_comes_from") or {}
check("...and that figure is the ledger's wages row, to the decimal",
      abs(_rwy[0]["but_it_pays_YOU"] - _led.get("_wages_for_your_own_work", -1)) < 0.06,
      (_rwy[0].get("but_it_pays_YOU"), sorted(_led)[:4]))
_rwy2 = [_ask(_game_c, cmd="why", id="horse_collar")]
check("...and a node that is NOT a held skill carries no such line",
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
s_vv = unopened_sim(capital=5000000.0)
s_vv.artisans = s_vv.scholars = 40.0
_opened = 0
for _k in sorted(node_id for node_id in NODES if NODES[node_id]["rev"] > 0):
    if _opened < 3 and s_vv.is_venture(_k):
        s_vv.done.add(_k)
        s_vv._done_changed()
        if s_vv.open_venture(_k)[0]:
            _opened += 1
check("three ventures opened for the screens to quote", _opened == 3, _opened)
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
s_cn = unopened_sim(capital=20000.0)
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
