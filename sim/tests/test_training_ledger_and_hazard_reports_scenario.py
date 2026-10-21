"""Scenarios: what a played game does with bought people, the revenue ledger, the start and stuck quotes, and the
replies that report them (Complaint 640: the rules are in test_training_ledger_and_hazard_reports)."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, with_end_year, pristine_game
from sim.refusal import cause_of
from sim.ui.proto.render_typed import render_pretty as _render_pretty

# --- scenario 1: bought people lose their training lag and the step names what left
# One game serves the reply, eminence, training-lag and ledger checks: each reads the same two years instead of
# playing its own.
_shared = sim(capital=500000.0, surveyed=())
run_it(_shared, "workshop_first", "freedman_staff")
_shared.done.add("fin_restaurant")
_shared.done.add("civ_road_paved")
_shared._done_changed()
_shared.labour.TRAINING_YEARS = 0.0   # the rows mature in the first step, where the old resync threw them away
_shared.labour.buy_slaves(12)
_at_purchase = _shared.artisans
_shared.eminence = _shared.cfg["eminence_danger"] * 0.9
with_end_year(_shared)
_ls = [ask_agent(_shared, cmd="start", id="hom_eraser_breadcrumb"), ask_agent(_shared, cmd="step", years=1)]
_conspicuous_logged = any(cause_of(message) == "eminence_warning" for _year, message in _shared.log)
_trained = _shared.artisans
_src = _shared.revenue_sources()
_revenue_total = _shared.revenue()
_shared.labour.manumit(12)
_shared.labour._resync_pools()
check("people you buy are worth nothing until they have learned the work",
      _at_purchase < 0.5, "%.2f craftsmen the day 12 were bought" % _at_purchase)
check("...and are worth something once they have, and do not vanish",
      _trained > 7.0, "%.2f craftsmen after the training lag" % _trained)
check("freeing them is worth more than holding them, as the model claims",
      _shared.artisans > _trained * 1.3,
      "%.2f held -> %.2f freed" % (_trained, _shared.artisans))
check("a step reports what left as well as what arrived",
      "lost" in _ls[-1], sorted(_ls[-1])[:12])
check("becoming conspicuous is logged as an eminence warning once eminence nears the danger line",
      _conspicuous_logged, [message for _year, message in _shared.log][-2:])
check("the ledger of a played year adds up to its stated revenue (the arithmetic is test_training_ledger_and_hazard_reports)",
      abs(sum(_src.values()) - _revenue_total) < 1.0,
      "rows %.1f against revenue %.1f" % (sum(_src.values()), _revenue_total))

# --- scenario 2: `start` and `stuck` quote one ceiling for a short trade
# arithmetic_positional wants more scribe-hours a year than the national ceiling, and sat at "81% spent" for a
# century. The engine knows this at start time.
_s_imp = unopened_sim(civ="england_1300")
for _p in NODES["arithmetic_positional"]["pre"]:
    _s_imp.done.add(_p)
_s_imp._done_changed()
_imp = S._agent_dispatch(_s_imp, NODES, {"cmd": "start", "id": "arithmetic_positional"})
check("starting work this society cannot staff says so at the time",
      _imp.get("ok") is True and "cannot supply the labour" in (_imp.get("but") or ""),
      _imp.get("but"))

# `start` quoted market_supply alone while its test weighed commissioned hours too, so `stuck` quoted a higher
# ceiling for the identical project a moment later.
s_lie = unopened_sim(capital=10000000.0)
for _p in NODES["logarithms"]["pre"]:
    s_lie.done.add(_p)
s_lie._done_changed()
s_lie.labour.hire("scholar", 2)
s_lie.labour.commission("scribe", 500.0)
_r_start = S._agent_dispatch(s_lie, NODES, {"cmd": "start", "id": "logarithms"})
_r_stuck = S._agent_dispatch(s_lie, NODES, {"cmd": "stuck"})
_but = _r_start.get("but") or ""
_stuck_why = ((_r_stuck.get("what_is_holding_you_up") or [{}])[0]
              .get("each_waiting_on", {}).get("logarithms", ""))
# presentation: the two commands quote the ceiling in words only; the number between "field" and "at most" is compared
check("the ceiling `start` quotes for a short trade is the one `stuck` quotes a moment later",
      _but and _stuck_why and
      _but.split("field ")[1].split(" at most")[0]
      == _stuck_why.split("field ")[1].split(" at most")[0],
      (_but, _stuck_why))

# --- scenario 3: the replies that report standing, help and a taught trade
_su = [ask_agent(pristine_game(), cmd="state")]
check("no dead field is reported every turn as though it were a mechanic",
      "suspicion" not in _su[0], [field_name for field_name in _su[0] if "susp" in field_name])
_he = [ask_agent(pristine_game(), cmd="help", topic="eminence")]
_hp = [ask_agent(pristine_game(), cmd="help", topic="protection")]
check("there is a help topic for eminence and one for protection",
      "eminence" in json.dumps(_he[0]).lower() and "no such topic" not in json.dumps(_he[0])
      and "no such topic" not in json.dumps(_hp[0]), (list(_he[0])[:4], list(_hp[0])[:3]))
_tn_game = unopened_sim(capital=2.0e6)
_tn = [ask_agent(_tn_game, cmd="train", trade="machinist", n=2), ask_agent(_tn_game, cmd="labour", trade="machinist")]
_row = (_tn[1].get("trade") or {})
check("a trade you taught is reported as existing here",
      _row.get("exists_here") is True, _row.get("exists_here"))
_pr_game = unopened_sim(capital=2.0e6)
_standing_before = _render_pretty("state", ask_agent(_pr_game, cmd="state", full=True))
ask_agent(_pr_game, cmd="bribe", amount=700)
_standing_after = _render_pretty("state", ask_agent(_pr_game, cmd="state", full=True))
_lines = [line for line in (_standing_before + "\n" + _standing_after).splitlines() if "STANDING:" in line]
# presentation: the standing line is the screen text a player reads
check("protection is on the screen that shows your standing",
      len(_lines) >= 2 and "protection" in _lines[0] and _lines[0] != _lines[1],
      _lines[:2])

# --- scenario 4: every cost breakdown multiplies out to the total it states
# A breakdown that omits a factor invites exactly this check and then fails it.
_bad_math = []
for _civ_m in ("england_1300", "rome_100ad", "norse_900ad"):
    _sm = unopened_sim(civ=_civ_m)
    for _k in ("clock_pendulum", "hot_air_balloon", "blast_furnace", "lens_grinding"):
        if _k not in NODES:
            continue
        _e = S._node_explain(_sm, NODES, _k)["cost"]
        # labour and capital take the civ and price factors; the missing materials are already at today's price
        _prod = (((_e["labour"] + _e["capital"]) * _e["civ_domain_factor"]
                  * _e["price_index"] + _e["materials"])
                 * _e["material_distance_factor"] * _e["opposition_factor"])
        if abs(_prod - _e["total"]) > max(2.0, _e["total"] * 0.005):
            _bad_math.append((_civ_m, _k, round(_prod, 1), _e["total"]))
check("every cost breakdown multiplies out to the total it states",
      not _bad_math, _bad_math[:3])
