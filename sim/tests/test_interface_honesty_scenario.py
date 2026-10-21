"""SCENARIO: what the protocol and screens tell a player in a real game is honest: fogged estimates are ranges, notes do not
rank themselves, prerequisites must be finished, progress and values are readable, and a step stops at a warning. Each
check reads the reply of a built game; the credit-warning rules are in `test_credit_warning_rules`."""
from .harness import *  # noqa: F401,F403
from sim.refusal import LogLine

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
_plain = sim()   # fog off, read only, shared by the checks that need an ordinary game
s_fe = sim()
s_fe.fog = True
s_fe.revealed = set()
_av_fe = S._agent_available(s_fe, NODES, {"all": True})
_est_rows = [row for row in _av_fe["available"] if isinstance(row["earns_per_year"], list)]
check("available quotes a range, not the true figure, for an unbuilt thing "
      "under fog",
      len(_est_rows) >= 1, len(_est_rows))
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
_asym = sum(1 for row in _est_rows
            if (s_fe.nodes[row["id"]]["rev"] - row["earns_per_year"][0])
            != (row["earns_per_year"][1] - s_fe.nodes[row["id"]]["rev"]))
check("the estimate is not a tight symmetric band centred on the truth - "
      "most of a real sample sit closer to one bound than the other",
      _asym >= len(_est_rows) * 0.5, "%d of %d" % (_asym, len(_est_rows)))

# UPKEEP STAYS EXACT. The user's question was specifically about payback
# (revenue); upkeep is closer to a quoted price, knowable in advance, and
# this project already keeps `cost` exact under fog for the same reason.
_k_up = next((row["id"] for row in _est_rows if s_fe.nodes[row["id"]]["up"] > 0), None)
if _k_up:
    _wu = S._agent_dispatch(s_fe, NODES, {"cmd": "why", "id": _k_up})
    # the crew's pay is in the payroll (Complaint 514), so a concern's upkeep is its non-crew share: the exact figure
    # is the one a game without fog quotes
    check("upkeep is exact under fog even for a thing you have never run",
          _wu["upkeep"] == _plain.venture_upkeep_quote(_k_up)["now"], (_wu["upkeep"], _plain.venture_upkeep_quote(_k_up)["now"]))

# NARROWS TO THE EXACT FIGURE ONCE YOU HAVE ACTUALLY RUN IT A FEW YEARS.
s_ry = s_fe
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
      not isinstance(_w_old["revenue"], list)
      and _w_old["revenue"] == round(s_ry.venture_real_earnings(_k_fe), 1), _w_old["revenue"])

# FOG OFF: the exact figure, as before.
s_nf = _plain
_w_nf = S._agent_dispatch(s_nf, NODES, {"cmd": "why", "id": _k_fe})
check("with fog off, EARNS/YR is still the exact figure",
      not isinstance(_w_nf["revenue"], list)
      and _w_nf["revenue"] == round(s_nf.venture_real_earnings(_k_fe), 1), _w_nf["revenue"])


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
    _wn = S._node_explain(_plain, NODES, _spid)
    check("%s's note no longer ranks itself against the rest of the tree"
          % _spid,
          all(banned_phrase not in (_wn.get("note") or "") for banned_phrase in _banned),
          _wn.get("note"))

# LEGITIMATE WARNINGS SURVIVE: plague_preparedness still tells you the date
# and what the node actually does about it - a consequence the player
# cannot see coming, not a ranking claim, and it must stay.
_pp = S._node_explain(_plain, NODES, "plague_preparedness")
# presentation: the hazard warning's wording
check("...but the actual hazard warning underneath it is untouched",
      "165 AD" in (_pp.get("note") or "")
      and "decides whether your institute survives" in (_pp.get("note") or ""),
      _pp.get("note"))

# school_founded's OWN statement that it is optional must survive too - it
# is the opposite of the fault being fixed.
_sf = S._node_explain(_plain, NODES, "school_founded")
check("school_founded's note still says it is optional",
      "OPTIONAL" in (_sf.get("note") or "")
      and "Nothing in the technical tree requires it" in (_sf.get("note") or ""),
      _sf.get("note"))

# UNDER FOG TOO: fog_summary takes its one sentence off the same note, and
# used to open with exactly the self-play line this exists to cut.
s_fp = s_fe
s_fp.revealed = {"school_founded"}
# presentation: the fogged summary's wording
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
    _dep = next((node_id for node_id in NODES if _cand in NODES[node_id]["pre"]), None)
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
      [line for line in _txt_pn.splitlines() if "FINISHED" in line] or _txt_pn[:200])


# --- JOB 3b: a fog-safe sense of progress DURING play, and nothing more
# until the run ends - the total itself is the size of the tree's own
# spoiler surface, same reasoning as downstream_count being hidden.
s_pg = s_fe
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
s_pg2 = _plain
_stpg2 = S._agent_dispatch(s_pg2, NODES, {"cmd": "state"})
check("with fog off, the fog-safe progress field is absent (path/why "
      "already answer this exactly, by name)",
      _stpg2.get("on_the_road_to_the_goal_so_far") is None, _stpg2)


# --- JOB 3c: the society's own values are readable. Event text has always
# named these fields directly ("changes the society: w_novelty") with no
# command that would say what one is; two testers asked for this.
_vals = S._agent_dispatch(_plain, NODES, {"cmd": "values"})
check("`values` exists and lists this society's own traits as numbers",
      _vals.get("ok") and len(_vals.get("values") or []) >= 8, _vals)
check("...and every field event text names is one this command can look up",
      {"w_novelty", "w_commerce", "w_magic_fear"} <=
      {row["field"] for row in _vals["values"]},
      [row["field"] for row in _vals["values"]])


# --- JOB 3d: a long step stops when something it warned about actually happens. The credit-exhausted line, the
# near-the-limit warning and the table of which lines stop a step are tested one at a time in
# test_credit_warning_rules.py (Complaint 640); the CLOSE TO THE LIMIT step below keeps the loop that reads the table.

# --- BREAK: the interrupt existed for the FATAL warning only.
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
_step_of_wn = s_wn.step


def _step_that_warns():
    """A year whose household ends it close to the limit: the line `warn_near_the_limit` writes (the rule that
    writes it is tested on its own in test_credit_warning_rules.py), so this step tests only the loop."""
    _step_of_wn()
    s_wn.state.household.log.append((s_wn.year, LogLine("credit_near_limit", "CLOSE TO THE LIMIT: test", share_of_limit=0.8)))


s_wn.step = _step_that_warns
_step_wn = S._agent_dispatch(s_wn, NODES, {"cmd": "step", "years": 50})
check("a multi-year step stops the moment it is CLOSE TO THE LIMIT too, not "
      "only once credit is fully exhausted",
      bool(_step_wn.get("stopped_early"))
      and any(event.get("event_kind") == "credit_near_limit" for event in _step_wn["events"])
      and not any(event.get("event_kind") == "credit_exhausted" for event in _step_wn["events"]),
      (_step_wn.get("stopped_early"),
       [event["message"] for event in _step_wn["events"]]))
check("...leaving most of the requested years unspent, not run through",
      _step_wn["year"] < s_wn.cfg["start_year"] + 100, _step_wn["year"])


