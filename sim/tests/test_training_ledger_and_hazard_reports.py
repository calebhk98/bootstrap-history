"""Training lag and people you buy, the revenue ledger, projects short of a trade or money, and how hazards, sackings and failures are reported."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, with_end_year, starved_game, pristine_game
from sim.ui.proto.render_typed import render_pretty as _render_pretty

# --- the Mexica play tester: a project's own accounting -----------------------
# Their three findings, each with the condition that produced it. All three need
# the SAME year to be short of a trade AND short of money, which is why none of
# them showed up in an ordinary run.


# 1. Hours could be refunded twice - once for the trade shortage and again for
#    the money - and both refunds were worked out from the hours OFFERED rather
#    than the hours actually taken off. The tester's project ended with 581.5
#    hours left against a 450-hour total, which the display read out as "-67%
#    of your hours spent". Here: 612.5 against 500 before the fix.
s = starved_game(9e5)
s.step()
_st = s.active.get("identity_cover") or {}
check("a project can never be given back more hours than it has spent",
      _st.get("ph_left", 0) <= NODES["identity_cover"]["ph"] + 1e-6,
      "%.1f left of a %.1f total" % (_st.get("ph_left", -1),
                                     NODES["identity_cover"]["ph"]))
check("an underfunded project says why it is underfunded",
      _st.get("underfunded_this_year") and "arrears" in (_st.get("why_underfunded") or ""),
      _st.get("why_underfunded"))

# 2. A shortage used to scale the PAYMENT rather than the instalment, so once
#    the balance was smaller than a year's instalment you paid a fraction of
#    what was left, every year, approaching zero without arriving - while
#    completion needs the bill under half a denarius. The tester watched one sit
#    at "71% done" for twenty-five years. Sixty years and 15.9 denarii still
#    owed, before the fix.
s = starved_game(60.0, supply=0.001, arrears=0.0, capital=500000.0)
s.active["identity_cover"]["ph_left"] = 0.0
for _i in range(12):
    s.step()
    if "identity_cover" not in s.active:
        break
check("a small remaining bill is actually paid off, not approached for ever",
      "identity_cover" not in s.active,
      "%.4f den still owed after 12 years"
      % (s.active.get("identity_cover", {}).get("cost_left", 0.0)))

# --- the Mexica play tester: advice you cannot act on is not advice ----------
# They were told the answer to the Spanish was "walls, firearms, powerful
# friends, and copies of your work kept somewhere else", played 154 years with
# 269 startable things in view, and reported finding no hedge of any kind. The
# hedges were there. Nothing ever connected the words to the list.
# 11 SECONDS: forty-five years of a Mexica optimizer run before the advice it
# is checking even has anything to say. The three checks that share that setup
# move together, since re-running it for each would cost three times as much.
def _hazard_advice_names_hedges():
    hazard_sim = sim(civ="mexica_1500", manual=False)
    hazard_sim.fog = True
    hazard_sim.revealed = set()
    counters = {node_id for node_id, _s2, _hazard_label in hazard_sim.HAZARD_COUNTERS["staff_loss"]}
    near = counters | {prereq_id for node_id in counters if node_id in NODES
                       for prereq_id in NODES[node_id]["pre"]}
    # Keep this focused on advice ordering rather than on which nodes the
    # revised civilization opening happens to reveal during the optimizer
    # run.  The player in the reported case had these candidate hedges in
    # view, so make that fixture condition explicit.
    hazard_sim.revealed.update(near)
    steps = (hazard_sim.hazard_advice("staff_loss")
             .get("you_could_begin_now_toward_it") or [])
    named = bool(steps) and all(
        step.get("id") and (step["can_begin_now"] or step.get("waiting_on"))
        for step in steps)
    ordered = [step["can_begin_now"] for step in steps] == sorted(
        (step["can_begin_now"] for step in steps), reverse=True)
    real = all(step["id"] in near for step in steps)
    return named and ordered and real, [
        (step["id"], step["can_begin_now"], (step.get("waiting_on") or "")[:40])
        for step in steps]

slow_check("a hazard names things in front of you that hedge against it, "
           "startable ones first, and every one really is a hedge",
           _hazard_advice_names_hedges)


# 5. Losing a finished work was silent. A tester lost fourteen inside one
#    `step 12`, corpus_written and school_founded among them, with every
#    arrival named and no departure named.
s = sim(capital=-50000.0, manual=False)
s.done.add("fin_restaurant")
s.done.add("civ_road_paved")
s._done_changed()
_lost_before = set(s.done)
with_end_year(s)
_ls = [ask_agent(s, cmd="start", id="hom_eraser_breadcrumb"), ask_agent(s, cmd="step", years=1)]
check("a step reports what left as well as what arrived",
      "lost" in _ls[-1], sorted(_ls[-1])[:12])

# 7. `suspicion` was replaced by `scandal` and then reported, unchanging, for
#    five hundred years. Two testers read a dead vestige as a broken mechanic.
_su = [ask_agent(pristine_game(), cmd="state")]
check("no dead field is reported every turn as though it were a mechanic",
      "suspicion" not in _su[0], [field_name for field_name in _su[0] if "susp" in field_name])

# --- the playtest-notes sweep -------------------------------------------------
# S1: every capital loss was written `capital *= x`, which is sign-blind. At
# minus a thousand denarii a sacking multiplied the DEBT by 0.4 and PAID the
# player six hundred, which made the deepest hole in the game the safest place
# to stand. Caught live twice in the notes: a Mexica sack -251 -> -100.5, an
# England thatch fire -629.2 -> -569.4.
s = sim()
s.capital = -1000.0
_gave = s.lose_capital(0.60)
check("a catastrophe never pays off a debt",
      s.capital == -1000.0 and _gave == 0.0,
      "capital %.1f, took %.1f" % (s.capital, _gave))
s.capital = 1000.0
s.lose_capital(0.60)
check("a catastrophe still takes its share of what you actually have",
      abs(s.capital - 400.0) < 1e-6, "%.1f" % s.capital)

# A1: hours_effective_this_year was `per - refunded`, and `per` is what was
# OFFERED, which may exceed what the project had left. The refunds are capped at
# spent_hours; this line was not, so a project reported 387.2 effective hours a
# year for four years while founder_hours_left never moved.
s = starved_game(9e5)
_before_left = s.active["identity_cover"]["ph_left"]
s.step()
_st3 = s.active.get("identity_cover") or {}
check("hours reported as effective are hours that actually came off the work",
      _st3.get("hours_effective_this_year", 0)
      <= _before_left - _st3.get("ph_left", 0) + 1e-6,
      "reported %.1f, actually %.1f"
      % (_st3.get("hours_effective_this_year", -1),
         _before_left - _st3.get("ph_left", 0)))

# --- the strategy order must actually put first what the goal needs first ----
# Han China reached the transistor in 0% of runs, and the reason was never
# economic: a run sat at year 700 holding 3.37 MILLION denarii, 57 scholars and
# 99 artisans, having never built cap_heat_1100 - tier 0, 225 denarii, two
# artisans, a prerequisite of the goal, and startable at any moment. It was at
# index 589 in the order the optimizer works down, because topo_stable was told
# nothing about the 128 nodes the strategy names explicitly and so could never
# place anything that depended on them. 100% after the fix.
_lab_o, _order_o, _b_o = S.load_strategy("recommended", NODES, GOAL)
_idx_o = {node_id: i for i, node_id in enumerate(_order_o)}
_viol = [(node_id, prereq_id) for node_id in _order_o for prereq_id in NODES[node_id]["pre"]
         if _idx_o.get(prereq_id, -1) > _idx_o[node_id]]
check("no technology is ordered before something it requires",
      not _viol, "%d violations, e.g. %s" % (len(_viol), _viol[:3]))
_need_o = S.closure(NODES, GOAL)
_last = max(_idx_o[node_id] for node_id in _need_o if node_id in _idx_o)
check("everything the goal needs is near the front, not spread over the tree",
      _last < 400, "the last goal-critical node sits at index %d of %d"
                   % (_last, len(_order_o)))

# ...and the fix must NOT be to close the grant over its prerequisites, which
# would hand Tenochtitlan sextants and cementation steel for nothing, because
# maize hangs off "cross the Atlantic and found a trading post".
_mx = sim(civ="mexica_1500")
check("a society is not granted the route another society would take to it",
      "cementation_steel" not in _mx.done and "clock_pendulum" not in _mx.done
      and "fud_maize" in _mx.done,
      [node_id for node_id in ("fud_maize", "cementation_steel", "clock_pendulum")
       if node_id in _mx.done])

# A hazard should report the harm it did to YOU, not the harm it would have
# done to somebody with something to lose: a tester with no staff and no money
# read "staff -45%, and 0 pence gone" three years running.
s = sim(civ="england_1300")
s.scholars = s.artisans = 0.0
s.employees = {}
s.capital = 0.0
s.year = 1348
s._shocks(1348)
_plague = [message for _year, message in s.log if "Black Death" in message]
check("a hazard that took nothing from you says so",
      not _plague or all("-45%" not in message or "nothing it could take" in message
                         for message in _plague),
      _plague)

# 2. Failure risk fired correctly and announced nothing, so a tester watched
#    about 113 builds, expected nine failures and found no occurrence of
#    "fail", "abandon" or "lost" anywhere, and concluded the mechanic was dead.
s = sim(capital=5000000.0)
_risky = [node_id for node_id in NODES if NODES[node_id]["risk"] >= 0.15][:1][0]
_fails = 0
for _i in range(120):
    s.active[_risky] = dict(ph_left=0.0, yrs=99.0, spent=0.0, cost_left=0.0)
    s.done.discard(_risky)
    s._complete(_risky)
    if _risky in s.active:
        _fails += 1
        del s.active[_risky]
check("a failed attempt is announced, not silently absorbed",
      _fails > 0 and any("FAILED at" in message for _year, message in s.log),
      "%d failures in 120 at risk %.2f, logged %d"
      % (_fails, NODES[_risky]["risk"],
         sum(1 for _year, message in s.log if "FAILED at" in message)))

# --- round 6, the England play tester ----------------------------------------
# 1. Bought people counted at full worth from the day of purchase, so the
#    training lag buy_slaves documents did nothing - and when a row finally
#    matured, step() added its capacity to self.artisans, which _resync_pools
#    then recomputed from scratch and threw away. A tester watched their
#    craftsmen fall from 35 to 3.8 at the moment the training finished.
s = sim(capital=500000.0)
run_it(s, "workshop_first", "freedman_staff")
s.labour.buy_slaves(12)
_at_purchase = s.artisans
for _ in range(4):
    s.step()
_trained = s.artisans
s.labour.manumit(12)
s.labour._resync_pools()
check("people you buy are worth nothing until they have learned the work",
      _at_purchase < 0.5, "%.2f craftsmen the day 12 were bought" % _at_purchase)
check("...and are worth something once they have, and do not vanish",
      _trained > 7.0, "%.2f craftsmen after the training lag" % _trained)
check("freeing them is worth more than holding them, as the model claims",
      s.artisans > _trained * 1.3,
      "%.2f held -> %.2f freed" % (_trained, s.artisans))

# 2. arithmetic_positional wants 2,500 scribe-hours a year against a national
#    ceiling of 1,321, and sat at "81% spent" from 1309 to about 1440. The
#    engine knows this at start time.
_s_imp = sim(civ="england_1300")
for _p in NODES["arithmetic_positional"]["pre"]:
    _s_imp.done.add(_p)
_s_imp._done_changed()
_imp = S._agent_dispatch(_s_imp, NODES, {"cmd": "start", "id": "arithmetic_positional"})
check("starting work this society cannot staff says so at the time",
      _imp.get("ok") is True and "cannot supply the labour" in (_imp.get("but") or ""),
      _imp.get("but"))

# --- BREAK: the fix above ("Make the stated labour ceiling the real one")
# changed the TEST here to weigh commissioned hours - hours_you_can_call_on,
# market_supply plus contract_hours - but left the NUMBER PRINTED reading
# market_supply alone. A player who had commissioned any of the short trade
# saw `start` quote one ceiling for a project and `stuck` quote a higher one
# for the identical project a moment later: the exact disagreement that
# commit's own message said could not happen again ("the statement and the
# arithmetic cannot disagree"). Reproduced directly: commission 500 scribe-
# hours (the project is still short), then start logarithms.
s_lie = sim(capital=10000000.0)
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
check("the ceiling `start` quotes for a short trade is the one `stuck` quotes a moment later",
      _but and _stuck_why and
      _but.split("field ")[1].split(" at most")[0]
      == _stuck_why.split("field ")[1].split(" at most")[0],
      (_but, _stuck_why))

# 3. The stat that ends the run had no warning and no help topic.
s = sim(capital=400.0)
s.eminence = s.cfg["eminence_danger"] * 0.9
s.step()
check("becoming conspicuous is said out loud before it kills you",
      any("BECOMING CONSPICUOUS" in message for _year, message in s.log),
      [message for _year, message in s.log][-2:])
_he = [ask_agent(pristine_game(), cmd="help", topic="eminence")]
check("...and there is a help topic for it",
      "eminence" in json.dumps(_he[0]).lower() and "no such topic" not in json.dumps(_he[0]),
      list(_he[0])[:4])

# A break tester summed what the ledger listed - 7,101.9 - against a stated
# revenue of 6,738 and reported that the accounts do not add up. They were
# right: it showed the fifteen largest rows and nothing else, so smaller
# concerns, the workshop's own output, state funding and the market saturation
# that caps the whole figure were all invisible.
# One year in, the game already has running earners and a market saturation gap to absorb; a
# longer run only costs time.
s = sim(civ="rome_100ad", manual=False)
s.step()
_src = s.revenue_sources()
check("the ledger's parts add up to the revenue it states, saturation gap included",
      "_what_the_market_will_not_absorb" in _src and abs(sum(_src.values()) - s.revenue()) < 1.0,
      "rows %.1f against revenue %.1f" % (sum(_src.values()), s.revenue()))

# A taught trade still read "does not exist yet" alongside "exists here: True".
_tn_game = sim(capital=2.0e6)
_tn = [ask_agent(_tn_game, cmd="train", trade="machinist", n=2), ask_agent(_tn_game, cmd="labour", trade="machinist")]
_row = (_tn[1].get("trade") or {})
check("a trade you taught does not still say it does not exist",
      _row.get("exists_here") is True
      and "does not exist yet" not in (_row.get("note") or ""),
      (_row.get("exists_here"), (_row.get("note") or "")[:60]))

# A break tester multiplied out the factors `why` shows for clock_pendulum,
# got 4,747.6 against a stated 4,834, and called it the one card in the game
# whose arithmetic does not work. It was: project_cost multiplies in a
# factor the breakdown never listed. A breakdown that
# omits a factor is worse than no breakdown, because it invites this exact
# check and then fails it.
_bad_math = []
for _civ_m in ("england_1300", "rome_100ad", "norse_900ad"):
    _sm = sim(civ=_civ_m)
    for _k in ("clock_pendulum", "hot_air_balloon", "blast_furnace", "lens_grinding"):
        if _k not in NODES:
            continue
        _e = S._node_explain(_sm, NODES, _k)["cost"]
        # labour and capital take the civ and price factors; the missing
        # materials are already at today's market price.
        _prod = (((_e["labour"] + _e["capital"]) * _e["civ_domain_factor"]
                  * _e["price_index"] + _e["materials"])
                 * _e["material_distance_factor"] * _e["opposition_factor"])
        if abs(_prod - _e["total"]) > max(2.0, _e["total"] * 0.005):
            _bad_math.append((_civ_m, _k, round(_prod, 1), _e["total"]))
check("every cost breakdown multiplies out to the total it states",
      not _bad_math, _bad_math[:3])

# --- round 7, the Rome weird-play tester -------------------------------------
# 1. `money`'s Net/yr omitted interest on arrears, with the interest RATE
#    printed two lines below it on the same screen. They read "+9.5 a year"
#    while capital fell 105, then 117, accelerating - a household in a debt
#    spiral being told it was recovering.
s = sim(civ="rome_100ad")
s.capital = -3000.0
_m = S._agent_dispatch(s, NODES, {"cmd": "money"})
check("the net counts interest on arrears, which is a cost like any other",
      _m["net_per_year"] < 0 and _m["what_it_costs_you"]["interest_on_arrears"] > 0,
      "net %.1f with %.1f of interest"
      % (_m["net_per_year"], _m["what_it_costs_you"]["interest_on_arrears"]))

# 5. "A site is sacked" took 62% of a tester's money, restarted every project
#    and cut their people nearly in half, and printed only those five words -
#    against a player who owned no sites. The plague family had already been
#    taught to report the harm it actually did; this one had not.
s = sim(civ="mexica_1500", capital=50000.0)
s.year = 1519
_dice_before_sacks = s.rng.getstate()
for _ in range(6):
    s._shocks(s.year)
    s.year += 1
_sacks = [message for _year, message in s.log if "sacked" in message]
check("a sacking says what it took from you",
      _sacks and ("taken" in _sacks[0] or "nothing it could take" in _sacks[0]),
      _sacks[:1])
# The same dice again on the same game, now with nothing to take.
s.rng.setstate(_dice_before_sacks)
s.capital = 0.0
s.year = 1519
_log_before_second_run = len(s.log)
for _ in range(6):
    s._shocks(s.year)
    s.year += 1
_sacks2 = [message for _year, message in s.log[_log_before_second_run:] if "sacked" in message]
check("...and says so plainly when it took nothing",
      _sacks2 and "nothing it could take" in _sacks2[0], _sacks2[:1])

# 6. `bribe` sells protection, protection decides whether strange work reads as
#    learning or as sorcery, and it appeared on no screen and in no help topic.
_pr_game = sim(capital=2.0e6)
_standing_before = _render_pretty("state", ask_agent(_pr_game, cmd="state", full=True))
ask_agent(_pr_game, cmd="bribe", amount=700)
_standing_after = _render_pretty("state", ask_agent(_pr_game, cmd="state", full=True))
_lines = [line for line in (_standing_before + "\n" + _standing_after).splitlines() if "STANDING:" in line]
check("protection is on the screen that shows your standing",
      len(_lines) >= 2 and "protection" in _lines[0] and _lines[0] != _lines[1],
      _lines[:2])
_hp = [ask_agent(pristine_game(), cmd="help", topic="protection")]
check("...and has a help topic of its own",
      "no such topic" not in json.dumps(_hp[0]), list(_hp[0])[:3])
