"""interface_honesty: split verbatim from the old test_regressions.py (original lines 8421-8670).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# ============================================================================
# INTERFACE HONESTY: an estimate instead of a certainty where fog says the
# player should not have one yet, the game not answering its own questions,
# and the smaller items testers asked for. protocol.py, fog.py.
# ============================================================================

# --- JOB 1: revenue is an estimate, not the true figure, for a thing you
# have never run, under fog. The user asked outright: "should you really be
# able to tell how much money you would make from researching something?
# Shouldn't the payback be something you don't know until after research?"
# and a break tester's own numbers said why it mattered - EARNS/YR under fog
# was "the only usable heuristic", and got them 95 of the 146 nodes on the
# road to the goal without working out the tree at all.
s_fe = sim()
s_fe.fog = True
s_fe.revealed = set()
_av_fe = S._agent_available(s_fe, NODES, {"all": True})
_est_rows = [r for r in _av_fe["available"] if isinstance(r["earns_per_year"], list)]
check("available quotes a range, not the true figure, for an unbuilt thing "
      "under fog",
      len(_est_rows) > 10, len(_est_rows))
_r0 = _est_rows[0]
check("...and the range is an actual range: low is really below high",
      _r0["earns_per_year"][0] < _r0["earns_per_year"][1], _r0)

_k_fe = _r0["id"]
_w1 = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_fe})
_w2 = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_fe})
check("the fogged estimate is deterministic - the same game asked the same "
      "question twice gets the same answer, not a fresh roll",
      _w1["revenue"] == _w2["revenue"], (_w1["revenue"], _w2["revenue"]))

# NOT A TIGHT SYMMETRIC BAND ON THE TRUTH: "400 +/- 50" gives the truth away
# just as plainly as the bare number did. Most of the range in a real sample
# has to sit CLOSER on one side than the other.
_asym = sum(1 for r in _est_rows
            if (NODES[r["id"]]["rev"] - r["earns_per_year"][0])
            != (r["earns_per_year"][1] - NODES[r["id"]]["rev"]))
check("the estimate is not a tight symmetric band centred on the truth - "
      "most of a real sample sit closer to one bound than the other",
      _asym >= len(_est_rows) * 0.5, "%d of %d" % (_asym, len(_est_rows)))

# UPKEEP STAYS EXACT. The user's question was specifically about payback
# (revenue); upkeep is closer to a quoted price, knowable in advance, and
# this project already keeps `cost` exact under fog for the same reason.
_k_up = next((r["id"] for r in _est_rows if NODES[r["id"]]["up"] > 0), None)
if _k_up:
    _wu = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_up})
    check("upkeep is exact under fog even for a thing you have never run",
          _wu["upkeep"] == NODES[_k_up]["up"], (_wu["upkeep"], NODES[_k_up]["up"]))

# NARROWS TO THE EXACT FIGURE ONCE YOU HAVE ACTUALLY RUN IT A FEW YEARS.
s_ry = sim()
s_ry.fog = True
s_ry.revealed = set()
s_ry.done.add(_k_fe)
s_ry.done_year[_k_fe] = s_ry.year
s_ry._done_changed()
_w_new = S._agent_dispatch(s_ry, NODES, {"cmd": "why", "id": _k_fe})
check("a freshly finished thing is still a guess - you have not run it yet",
      isinstance(_w_new["revenue"], list), _w_new["revenue"])
s_ry.year += 3
_w_old = S._agent_dispatch(s_ry, NODES, {"cmd": "why", "id": _k_fe})
check("...and becomes the exact figure after you have actually run it a "
      "few years",
      _w_old["revenue"] == NODES[_k_fe]["rev"], _w_old["revenue"])

# FOG OFF: the exact figure, as before.
s_nf = sim()
_w_nf = S._agent_dispatch(s_nf, NODES, {"cmd": "why", "id": _k_fe})
check("with fog off, EARNS/YR is still the exact figure",
      _w_nf["revenue"] == NODES[_k_fe]["rev"], _w_nf["revenue"])


# --- JOB 2: the game must not tell you which branch matters most. A
# normal-play tester quoted school_founded's own note calling itself "the
# pivot of the entire game" with "every year of delay here costs more than
# any single technology"; corpus_dispersed, corpus_written and
# plague_preparedness rank themselves the same way.
for _spid, _banned in (
        ("school_founded", ("pivot of the entire game",
                            "costs more than any single",
                            "highest-leverage thing you can spend money on")),
        ("corpus_dispersed", ("highest expected-value node in the tree",)),
        ("corpus_written", ("largest single call on your personal hours",
                            "must not cut")),
        ("plague_preparedness", ("highest expected-value defensive investment",))):
    _wn = S._node_explain(sim(), NODES, _spid)
    check("%s's note no longer ranks itself against the rest of the tree"
          % _spid,
          all(b not in (_wn.get("note") or "") for b in _banned),
          _wn.get("note"))

# LEGITIMATE WARNINGS SURVIVE: plague_preparedness still tells you the date
# and what the node actually does about it - a consequence the player
# cannot see coming, not a ranking claim, and it must stay.
_pp = S._node_explain(sim(), NODES, "plague_preparedness")
check("...but the actual hazard warning underneath it is untouched",
      "165 AD" in (_pp.get("note") or "")
      and "decides whether your institute survives" in (_pp.get("note") or ""),
      _pp.get("note"))

# school_founded's OWN statement that it is optional must survive too - it
# is the opposite of the fault being fixed.
_sf = S._node_explain(sim(), NODES, "school_founded")
check("school_founded's note still says it is optional",
      "OPTIONAL" in (_sf.get("note") or "")
      and "Nothing in the technical tree requires it" in (_sf.get("note") or ""),
      _sf.get("note"))

# UNDER FOG TOO: fog_summary takes its one sentence off the same note, and
# used to open with exactly the self-play line this exists to cut.
s_fp = sim()
s_fp.fog = True
s_fp.revealed = {"school_founded"}
check("the fogged one-line summary of school_founded is not its own "
      "self-rating either",
      "pivot" not in s_fp.fog_summary("school_founded").lower(),
      s_fp.fog_summary("school_founded"))


# --- JOB 3a: a prerequisite has to be DONE, not merely started. A tester
# wrote "nothing states whether a prerequisite must be DONE or open" - it
# has always meant done, and the one sentence that said so lived only in a
# branch start_blocked_reason pre-empts on every ordinary refusal, so a
# player who actually hit the refusal never saw it.
s_pn = sim(capital=1000000.0)
_pair_pn = None
for _cand in s_pn.order:
    if not s_pn.can_start(_cand):
        continue
    _dep = next((m for m in NODES if _cand in NODES[m]["pre"]), None)
    if _dep:
        _pair_pn = (_cand, _dep)
        break
_k1_pn, _k2_pn = _pair_pn
S._agent_dispatch(s_pn, NODES, {"cmd": "start", "id": _k1_pn})
_w_pn = S._node_explain(s_pn, NODES, _k2_pn)
_txt_pn = _RP("why", _w_pn)
check("a refusal for a started-but-unfinished prerequisite says it has to "
      "be FINISHED, not merely started - on the path a player actually hits",
      "FINISHED" in _txt_pn and "not merely started" in _txt_pn,
      [ln for ln in _txt_pn.splitlines() if "FINISHED" in ln] or _txt_pn[:200])


# --- JOB 3b: a fog-safe sense of progress DURING play, and nothing more
# until the run ends - the total itself is the size of the tree's own
# spoiler surface, same reasoning as downstream_count being hidden.
s_pg = sim()
s_pg.fog = True
s_pg.revealed = set()
s_pg.done.add("arithmetic_positional")
s_pg._done_changed()
_stpg = S._agent_dispatch(s_pg, NODES, {"cmd": "state"})
check("under fog, `state` says how many of the goal's road you already have",
      isinstance(_stpg.get("on_the_road_to_the_goal_so_far"), int)
      and _stpg["on_the_road_to_the_goal_so_far"] >= 1,
      _stpg.get("on_the_road_to_the_goal_so_far"))
check("...but never the total - final_report gives that, once the run is "
      "over and there is nothing left to spoil",
      "the_whole_road_was" not in _stpg, sorted(_stpg.keys()))
s_pg2 = sim()
_stpg2 = S._agent_dispatch(s_pg2, NODES, {"cmd": "state"})
check("with fog off, the fog-safe progress field is absent (path/why "
      "already answer this exactly, by name)",
      _stpg2.get("on_the_road_to_the_goal_so_far") is None, _stpg2)


# --- JOB 3c: the society's own values are readable. Event text has always
# named these fields directly ("changes the society: w_novelty") with no
# command that would say what one is; two testers asked for this.
_vals = S._agent_dispatch(sim(), NODES, {"cmd": "values"})
check("`values` exists and lists this society's own traits as numbers",
      _vals.get("ok") and len(_vals.get("values") or []) >= 8, _vals)
check("...and every field event text names is one this command can look up",
      {"w_novelty", "w_commerce", "w_magic_fear"} <=
      {r["field"] for r in _vals["values"]},
      [r["field"] for r in _vals["values"]])


# --- JOB 3d: a long step stops when something it warned about actually
# happens, rather than running the rest of the years you asked for on top
# of it. A break tester watched "CLOSE TO THE LIMIT ... while it is still
# your choice" get ploughed straight through to CREDIT EXHAUSTED inside one
# big `step`.
s_se = sim(capital=500.0)
s_se.end_year = s_se.cfg["start_year"] + 200
# Plain `start`, not `rush` - this check has to stand on its own before
# `rush` exists as a command (see JOB 3f, committed separately and later).
_memo_se = {}
_ok_se = [k for k in s_se.order if s_se.can_start(k, _memo=_memo_se)]
_ok_se = [k for k in _ok_se
          if not (NODES[k]["ph"] == 0 and NODES[k]["_total_cost"] <= 1)]
_ok_se.sort(key=lambda k: s_se.project_cost(k), reverse=True)
for _k_se in _ok_se[:15]:
    S._agent_dispatch(s_se, NODES, {"cmd": "start", "id": _k_se})
_step_ce = S._agent_dispatch(s_se, NODES, {"cmd": "step", "years": 100})
# CLOSE TO THE LIMIT now interrupts a batched step too (see the dedicated
# check below), and it fires strictly BEFORE exhaustion by design - so this
# same household may now stop there first, on the way to the exhaustion
# this test is actually about. Keep stepping through any such earlier stop;
# the property under test is that it reaches, and stops AT, exhaustion
# eventually, never running past it within one call.
_saw_exhausted = any("CREDIT EXHAUSTED" in e["message"] for e in _step_ce["events"])
_hops = 0
while (not _saw_exhausted and _step_ce.get("stopped_early")
       and s_se.year < s_se.end_year and _hops < 20):
    _step_ce = S._agent_dispatch(s_se, NODES,
                                 {"cmd": "step",
                                  "years": min(100, s_se.end_year - s_se.year)})
    _saw_exhausted = any("CREDIT EXHAUSTED" in e["message"]
                        for e in _step_ce["events"])
    _hops += 1
check("a multi-year step stops the moment credit is actually exhausted, "
      "rather than running the rest of the years on top of it",
      bool(_step_ce.get("stopped_early")) and _saw_exhausted,
      (_step_ce.get("stopped_early"), _hops))
check("...and it really did stop short of the 100 years asked for",
      s_se.year < s_se.cfg["start_year"] + 100, s_se.year)

# --- BREAK: the interrupt above existed for the FATAL warning only.
# warn_near_the_limit's own docstring says it exists to give you a chance to
# react "while there is still a decision left" - stop a project, mothball a
# loss-maker, fire somebody - and it fired into the log exactly as promised,
# but a batched `step` read straight past it and kept running, so the
# decision it offered was gone four years before the player's next turn,
# when CREDIT EXHAUSTED (which DID interrupt) finally showed up. Two players
# on two different civilisations reported this independently. The warning
# that still leaves you a choice is the one that most needs to interrupt;
# the fatal one needs it least, since nothing is left to choose by then.
s_wn = sim(capital=500.0)
s_wn.end_year = s_wn.cfg["start_year"] + 200
_lim_wn = s_wn.credit_limit()
# Set up just past the 70% warning threshold, comfortably short of the 100%
# that would also trip CREDIT EXHAUSTED in the same year - the two markers
# have to be tested apart, or a step that stops for the wrong reason would
# still pass.
s_wn.capital = -(0.85 * _lim_wn)
_step_wn = S._agent_dispatch(s_wn, NODES, {"cmd": "step", "years": 50})
check("a multi-year step stops the moment it is CLOSE TO THE LIMIT too, not "
      "only once credit is fully exhausted",
      bool(_step_wn.get("stopped_early"))
      and any("CLOSE TO THE LIMIT" in e["message"] for e in _step_wn["events"])
      and not any("CREDIT EXHAUSTED" in e["message"] for e in _step_wn["events"]),
      (_step_wn.get("stopped_early"),
       [e["message"] for e in _step_wn["events"]]))
check("...leaving most of the requested years unspent, not run through",
      _step_wn["year"] < s_wn.cfg["start_year"] + 100, _step_wn["year"])


