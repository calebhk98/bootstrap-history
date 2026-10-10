"""project_retry_and_risk: regression checks, run individually with `--only project_retry_and_risk`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO
from sim.engine.industry_depth import RISK_SHARE_AT_FULL_DEPTH

# --- a failed attempt teaches you something (projects.py: retry learning) ---
# A player who had already won the game: a failed high-pressure steam system
# used to reset the calendar floor to zero and roll again at the identical
# probability, as if the first attempt had never happened. Now failed_attempts
# (counted since before this round, never spent) buys BOTH a smaller chance of
# failing the same way twice and a banked share of the calendar clock - see
# projects.py's own section comment on _complete for the full reasoning.
_s_rl = sim(capital=10 ** 9)
_rl_k = [node_id for node_id in NODES if NODES[node_id]["risk"] >= 0.15][0]
# A diagnosed failure adds its attempt's worker-years to the industry's tenure stock, which
# is all the risk reads; walk the sequence forward by adding them rather than rolling dice.
_seq = []
for _m in range(5):
    _s_rl.failed_attempts[_rl_k] = _m
    _seq.append(_s_rl.effective_risk(_rl_k))
    _s_rl.learn_from_failed_attempt(_rl_k)
check("attempt one faces the bare, untrained risk - nothing has been "
      "learned yet because nothing has failed yet",
      _seq[0] == NODES[_rl_k]["risk"], _seq[0])
check("each later attempt's risk is strictly lower than the one before it, "
      "and a fourth attempt (three failures in) is meaningfully better than "
      "the first, not just marginally",
      all(_seq[i] < _seq[i - 1] for i in range(1, 5))
      and _seq[3] <= _seq[0] * 0.95, _seq)
check("...but it is never a guarantee: risk never reaches zero, bounded "
      "below by RISK_SHARE_AT_FULL_DEPTH's own share of the bare risk",
      all(risk_value >= NODES[_rl_k]["risk"] * RISK_SHARE_AT_FULL_DEPTH - 1e-9 for risk_value in _seq),
      _seq)
_s_rl.failed_attempts[_rl_k] = 0
_s_rl.state.projects.tenure.clear()

class _AlwaysFails(random.Random):
    """0.0 is below every risk the tree defines, so this fails every roll -
    the mirror image of path_search.py's own DetRNG, which returns 1.0 to
    never fail anything."""
    def random(self):
        return 0.0


_s_cal = _s_rl
_cal_k = [node_id for node_id in NODES if NODES[node_id]["risk"] >= 0.15 and NODES[node_id]["yrs"] >= 5][0]
_cal_floor = NODES[_cal_k]["yrs"]
_s_cal.rng = _AlwaysFails()
_banked = []
for _ in range(4):
    _s_cal.active[_cal_k] = dict(ph_left=0.0, yrs=_cal_floor, spent=0.0,
                                 cost_left=0.0)
    _s_cal.done.discard(_cal_k)
    _s_cal._complete(_cal_k)
    _banked.append(_s_cal.active[_cal_k]["yrs"])
check("even the FIRST failure already banks a real share of the elapsed "
      "clock - the social groundwork a failed attempt leaves behind does "
      "not vanish with it",
      0 < _banked[0] < _cal_floor, (_banked, _cal_floor))
check("every later failure banks MORE of the clock than the one before, "
      "with shrinking increments, and never the full floor",
      all(_banked[i] > _banked[i - 1] for i in range(1, 4))
      and all(banked_value < _cal_floor for banked_value in _banked), (_banked, _cal_floor))
check("...capped well short of the whole floor - RETRY_CALENDAR_CAP's own "
      "share - so a retried programme is readier, never instantly ready",
      _banked[-1] <= _cal_floor * _s_cal.RETRY_CALENDAR_CAP + 1e-6, _banked)

# --- a hazard timeline that escalates, instead of reading the same at 150 --
# years out and at 5 (society.py: hazard_timeline, wired into fog.py's
# knowledge_risk as the `risk` command's "timeline"). A Rome player watched
# "hedged by nothing yet" sit unchanged for a hundred and fifty years and
# lost a third of their progress the year the hazard landed anyway; the fix
# is that the SAME hazard's own words change as the gap between "when it
# lands" and "how long the hedge takes" closes.
_s_tl = sim(civ="rome_100ad")
_s_tl.year = 150
_tl_far = next((entry for entry in _s_tl.hazard_timeline()
               if entry["name"] == "Third century crisis"), None)
_s_tl.year = 234
_tl_near = next((entry for entry in _s_tl.hazard_timeline()
                 if entry["name"] == "Third century crisis"), None)
check("hazard_timeline names the Third century crisis while it is still "
      "visibly ahead and again once it is nearly here",
      _tl_far is not None and _tl_near is not None, (_tl_far, _tl_near))
check("the SAME hazard's urgency tag escalates as the date closes in - "
      "'on the horizon' far out, something sharper once even the fastest "
      "hedge could no longer finish in time",
      _tl_far and _tl_near and _tl_far["urgency"] != _tl_near["urgency"]
      and _tl_far["urgency"] in ("on the horizon", "hedged")
      and _tl_near["urgency"] in ("too late to hedge", "stopgap only",
                                  "begin hedge now", "happening now"),
      (_tl_far, _tl_near))
check("hazard_timeline is sorted nearest first",
      [entry["years_until"] for entry in _s_tl.hazard_timeline()]
      == sorted(entry["years_until"] for entry in _s_tl.hazard_timeline()),
      [entry["years_until"] for entry in _s_tl.hazard_timeline()])
_rk_tl = S._agent_dispatch(_s_tl, NODES, {"cmd": "risk"})
check("the `risk` command itself carries the compact timeline, not just "
      "the per-kind breakdown",
      isinstance(_rk_tl.get("knowledge_risk", {}).get("timeline"), list)
      and len(_rk_tl["knowledge_risk"]["timeline"]) > 0, _rk_tl.get("knowledge_risk"))

# RETRY LEARNING HAS TO SURVIVE A SAVE. failed_attempts drives
# _retry_calendar_retain and the tenure stock, and it was not in
# SAVE_FIELDS, so every resume reset the household to "nothing has ever been
# tried". The player who won the game reported repeated 45% failures with "no
# strategic mitigation visible": the mitigation was there and the save
# round-trip was deleting it.
import collections as _coll
from sim.ui import protocol as _PROTO

_fa_path = os.path.join(HERE, "_fa_roundtrip.json")
_s_fa = sim()
_s_fa.failed_attempts["zone_refining"] = 3
for _ in range(3):
    _s_fa.learn_from_failed_attempt("zone_refining")
_s_fa.shortages["iron"] = 7
_risk_before = _s_fa.effective_risk("zone_refining")
_cal_before = _s_fa._retry_calendar_retain("zone_refining")
_PROTO.save_state(_s_fa, _fa_path)
_s_fa2 = sim()
_PROTO.load_state(_s_fa2, _fa_path)
check("three failures on zone_refining still stand after a save and a "
      "resume, so the next attempt is the risk the learning bought and not "
      "the bare 45%",
      abs(_s_fa2.effective_risk("zone_refining") - _risk_before) < 1e-9
      and _risk_before < NODES["zone_refining"]["risk"] - 1e-6,
      (_risk_before, _s_fa2.effective_risk("zone_refining")))
check("the calendar already spent on those attempts survives the resume too",
      abs(_s_fa2._retry_calendar_retain("zone_refining") - _cal_before) < 1e-9
      and _cal_before > 0.5,
      (_cal_before, _s_fa2._retry_calendar_retain("zone_refining")))
check("a resumed save can still count a NEW failure: the accumulators come "
      "back as a defaultdict and a Counter, not as the plain dicts JSON "
      "hands back, which would raise KeyError on the first += ",
      (isinstance(_s_fa2.failed_attempts, _coll.defaultdict)
       and isinstance(_s_fa2.shortages, _coll.Counter)),
      (type(_s_fa2.failed_attempts).__name__, type(_s_fa2.shortages).__name__))
_s_fa2.failed_attempts["never_seen_node"] += 1
_s_fa2.shortages["never_seen_material"] += 1
check("and incrementing an id the save never mentioned works rather than "
      "raising",
      _s_fa2.failed_attempts["never_seen_node"] == 1
      and _s_fa2.shortages["never_seen_material"] == 1,
      (dict(_s_fa2.failed_attempts), dict(_s_fa2.shortages)))
check("the diagnostic shortage tally is continuous across a resume as well",
      _s_fa2.shortages.get("iron") == 7, dict(_s_fa2.shortages))
try:
    os.remove(_fa_path)
except OSError:
    pass

# AND THE CLASS, NOT JUST THE INSTANCE. Both fields that were missing are
# accumulators - a defaultdict and a Counter that code does `+= 1` into - and
# that is the shape of state most likely to be added without anyone
# remembering the save contract. Any future one has to be saved or
# deliberately named here, rather than silently resetting every resume.
#
# BOTH `vars(sim())` AND `vars(sim().household)`, since the household
# extraction (see docs/architecture/HOUSEHOLD_EXTRACTION.md) moved both of
# the accumulators this check was written for - failed_attempts and
# shortages - off `Sim` itself and onto `Sim.household`. Scanning `Sim`
# alone here would silently stop catching a future accumulator the moment it
# is added to the household rather than to the world, which is exactly the
# blind spot this comment says must not exist.
_NOT_SAVED_ON_PURPOSE = frozenset()
_fresh = _s_fa
_accum = {attr_name for attr_name, value in vars(_fresh).items()
          if isinstance(value, (_coll.defaultdict, _coll.Counter))}
_accum |= {attr_name for attr_name, value in vars(_fresh.household).items()
           if isinstance(value, (_coll.defaultdict, _coll.Counter))}
check("every accumulator a fresh Sim carries is either in SAVE_FIELDS or "
      "listed as deliberately unsaved, so the next one added cannot quietly "
      "reset on every resume the way retry learning did",
      _accum <= (set(_PROTO.SAVE_FIELDS) | _NOT_SAVED_ON_PURPOSE),
      sorted(_accum - (set(_PROTO.SAVE_FIELDS) | _NOT_SAVED_ON_PURPOSE)))
# ======================================================================
# ROUND 9: expected calendar cost of a risky node, including retries
# (projects.py: calendar_floor, expected_calendar_years). A 45%-risk,
# 4-year-floor node is not a 4-year project - the raw geometric series
# 1/(1-p) says 1.82 attempts, and even that is wrong once retry learning
# (RISK_SHARE_AT_FULL_DEPTH, RETRY_CALENDAR_CAP) starts changing the odds and the
# wait on every attempt after the first. Verified both in closed form and,
# separately in a throwaway Monte Carlo harness during development, against
# thousands of real _complete() calls - see the session's own report for
# those numbers; what is pinned here is the cheap, deterministic shape of
# the guarantee, not a re-run of the simulation on every gate pass.
# ======================================================================
_s_ey = sim(civ="rome_100ad")
_riskfree = next(node_id for node_id in NODES if NODES[node_id].get("risk", 1) == 0)
check("risk-free node: expected calendar years is exactly the earliest completion - "
      "there is nothing to retry",
      abs(_s_ey.expected_calendar_years(_riskfree)
          - _s_ey.earliest_completion_years(_riskfree)) < 1e-9,
      (_riskfree, _s_ey.expected_calendar_years(_riskfree),
       _s_ey.earliest_completion_years(_riskfree)))
_pct_floor = _s_ey.calendar_floor("point_contact_transistor")
_pct_exp = _s_ey.expected_calendar_years("point_contact_transistor")
check("a risky node's expected calendar cost is strictly more than its bare "
      "floor (point_contact_transistor: 45% risk, 4-year floor)",
      _pct_exp > _pct_floor, (_pct_exp, _pct_floor))
check("...but retry learning means it is LESS than the naive geometric "
      "series 1/(1-p) on the raw risk would predict - neither odds nor wait "
      "stay fixed across retries the way a plain geometric series assumes",
      _pct_exp < _pct_floor / (1.0 - NODES["point_contact_transistor"]["risk"]),
      (_pct_exp, _pct_floor / (1.0 - NODES["point_contact_transistor"]["risk"])))
# INDEPENDENTLY RE-DERIVED THROUGH effective_risk ITSELF, never through a
# copy of whatever formula happens to live inside it today. effective_risk
# is the one place allowed to know every multiplier a node's odds carry -
# retry learning today, and it is the designated home for anything else a
# later change adds (a capability that makes a family of processes more
# reliable, say) - so a second check of expected_calendar_years has to ask
# the SAME function the same way it does: stand in for "m failures so far"
# by setting failed_attempts, read effective_risk, move on. A check that
# instead hard-codes RISK_SHARE_AT_FULL_DEPTH would pass today and go on
# passing while silently checking the wrong thing the moment any other
# multiplier joins effective_risk.
_pct_node = "point_contact_transistor"
_manual_total, _manual_survive, _i = 0.0, 1.0, 0
_cc, _cd = _s_ey.RETRY_CALENDAR_CAP, _s_ey.RETRY_CALENDAR_DECAY
_saved_fa = _s_ey.failed_attempts.get(_pct_node, 0)
while _manual_survive > 1e-15:
    _a = _pct_floor if _i == 0 else _pct_floor * (1.0 - _cc * (1.0 - _cd ** _i))
    _manual_total += _manual_survive * _a
    _s_ey.failed_attempts[_pct_node] = _i
    with _s_ey.after_failed_attempts(_pct_node, _i):
        _manual_survive *= _s_ey.effective_risk(_pct_node)
    _i += 1
_s_ey.failed_attempts[_pct_node] = _saved_fa
check("expected_calendar_years matches an independent sum driven by "
      "effective_risk() at each hypothetical attempt count, not a "
      "hard-coded copy of the retry-learning formula, to within float "
      "rounding",
      abs(_pct_exp - _manual_total) < 1e-6, (_pct_exp, _manual_total))
check("...and expected_calendar_years itself leaves the real failure count "
      "exactly as it found it once the projection is done - a read-only "
      "query, not a mutation disguised as one",
      _s_ey.failed_attempts.get(_pct_node, 0) == _saved_fa,
      _s_ey.failed_attempts.get(_pct_node, 0))
_s_ey2 = _s_ey
_s_ey2.failed_attempts["point_contact_transistor"] = 3
for _ in range(3):
    _s_ey2.learn_from_failed_attempt("point_contact_transistor")
check("...concretely: 3 prior failures leaves less EXPECTED remaining "
      "calendar time than attempt one alone faced, not more",
      _s_ey2.expected_calendar_years("point_contact_transistor") < _pct_exp,
      (_s_ey2.expected_calendar_years("point_contact_transistor"), _pct_exp))
_s_ey.failed_attempts["point_contact_transistor"] = _saved_fa
_s_ey.state.projects.tenure.clear()
check("calendar_floor is the SAME figure core.py's step() gates completion "
      "on - not a second copy of the reputation-shrinking formula",
      _s_ey.calendar_floor("zone_refining")
      == max(2.0, NODES["zone_refining"]["yrs"] / (1.0 + _s_ey.reputation / 90.0))
      if NODES["zone_refining"]["yrs"] >= 5 else
      _s_ey.calendar_floor("zone_refining") == NODES["zone_refining"]["yrs"],
      _s_ey.calendar_floor("zone_refining"))
# Surfaced wherever risk and years already are: `why`, `available` (fog and
# not), and the `start` confirmation - not a fifth screen nobody reads.
_why_pct = S._agent_dispatch(_s_ey, NODES, {"cmd": "why", "id": "point_contact_transistor"})
check("`why` shows the expected total calendar years including retries, "
      "alongside the bare floor, not instead of it",
      _why_pct.get("calendar_floor_years") == NODES["point_contact_transistor"]["yrs"]
      and _why_pct.get("expected_calendar_years_with_retries") is not None
      and _why_pct["expected_calendar_years_with_retries"] > _why_pct["calendar_floor_years"],
      _why_pct.get("expected_calendar_years_with_retries"))
# ======================================================================
# ROUND 10: the first-timer tip about `help commands` and `log` is said ONCE
# early in a run, not every turn and not to a player deep into a run.
# ======================================================================
_s_wk = sim(civ="rome_100ad")
_st1 = S._agent_dispatch(_s_wk, NODES, {"cmd": "state"})
check("a fresh game's very first `state` points at `help commands` and "
      "`log` directly, in the reply itself",
      bool(_st1.get("worth_knowing_early"))
      and "help" in _st1["worth_knowing_early"] and "log" in _st1["worth_knowing_early"],
      _st1.get("worth_knowing_early"))
_st2 = S._agent_dispatch(_s_wk, NODES, {"cmd": "state"})
check("...but only ONCE - the second call in the same early game says "
      "nothing more about it, so it never becomes per-turn noise",
      _st2.get("worth_knowing_early") is None, _st2.get("worth_knowing_early"))
check("the one-shot flag is in SAVE_FIELDS, so it survives a save/load and "
      "does not fire a second time just because the process restarted",
      "_said_command_index" in _protocol.SAVE_FIELDS, None)
_s_wk._said_command_index = False
_s_wk.year = _s_wk.cfg["start_year"] + 50
_st_late = S._agent_dispatch(_s_wk, NODES, {"cmd": "state"})
check("resuming deep into an existing run (year far past the opening) never "
      "springs this first-timer tip on a player who has long since found "
      "all of this themselves",
      _st_late.get("worth_knowing_early") is None, _st_late.get("worth_knowing_early"))

# ======================================================================
# ROUND 11: point_contact_transistor no longer waits on single_crystal or
# silicon_path in the live engine (the tree data is pinned in round8g_display).
# ======================================================================
_s_pct = sim(civ="rome_100ad", capital=10_000_000.0)
for _p in NODES["point_contact_transistor"]["pre"]:
    _s_pct.done.add(_p)
_s_pct._done_changed()
_s_pct.scholars, _s_pct.artisans = 200.0, 200.0
_s_pct.trades_created.update(["chemist", "machinist"])
_s_pct.employees["chemist"], _s_pct.employees["machinist"] = 20.0, 20.0
_ok_pct, _why_pct2 = _s_pct.start_reason("point_contact_transistor")
check("with every listed prerequisite met and nothing else missing, "
      "start_reason actually allows it - the live engine, not just the "
      "tree data, agrees single_crystal/silicon_path are not required",
      _ok_pct, _why_pct2)
# A FREE PREREQUISITE SHOULD SAY IT IS FREE. Eight cap_* nodes cost nothing,
# take no time and cannot fail, and a player still has to start each by hand.
# The player who won this game called the refusal that names one of them
# "administrative": it said "missing prerequisites: cap_measure_temp" and
# nothing about the thing behind that name being one free command away. They
# are not auto-granted, because each carries 20 a year of upkeep if it is ever
# opened and that is the player's decision to make, and they never need
# opening to satisfy a prerequisite (start_reason tests `p not in self.done`).
_s_fp = sim()          # thermometer NOT done, so cap_measure_temp is blocked
_, _fp_why2 = _s_fp.start_reason("chm_crystallisation")
check("a free node that is itself blocked is not offered as the next step, "
      "which would be a second refusal wearing the first one's clothes",
      "costs nothing" not in (_fp_why2 or ""), _fp_why2)
_, _fp_why3 = _s_fp.start_reason("junction_transistor")
check("an ordinary expensive prerequisite gets no such hint",
      "costs nothing" not in (_fp_why3 or ""), _fp_why3)
_s_fp.done.add("thermometer"); _s_fp._done_changed()
_, _fp_why = _s_fp.start_reason("chm_crystallisation")
check("a refusal whose missing prerequisite is free, instant and startable "
      "now says so and gives the command, instead of naming it and stopping",
      "costs nothing, takes no time and cannot fail" in (_fp_why or "")
      and "start cap_measure_temp" in (_fp_why or ""), _fp_why)

# UNDER FOG IT MAY NOT NAME WHAT THE PLAYER CANNOT SEE.
_s_fp.fog = True
_s_fp.revealed = set()
_fp_hidden = [node_id for node_id in ("cap_measure_temp", "cap_measure_elec",
                          "cap_power_water", "cap_power_steam")
              if not _s_fp.is_visible(node_id)]
_fp_msgs = []
for _k in sorted(NODES):
    if any(hidden_id in NODES[_k]["pre"] for hidden_id in _fp_hidden):
        _, _w = _s_fp.start_reason(_k)
        if _w:
            _fp_msgs.append(_w)
check("under fog the free-prerequisite hint never names a capability the "
      "player has not heard of",
      bool(_fp_hidden) and not any(hidden_id in message for message in _fp_msgs for hidden_id in _fp_hidden),
      (_fp_hidden, _fp_msgs[:2]))

# AND THE PREMISE. If one of these ever acquires a cost, the sentence above
# stops being true, so the set it describes has to stay genuinely free.
_fp_free = [node_id for node_id, node in NODES.items()
            if node_id.startswith("cap_") and (node.get("_total_cost") or 0) <= 1
            and (node.get("ph") or 0) == 0 and (node.get("yrs") or 0) == 0
            and (node.get("risk") or 0) == 0]
check("the free capability nodes the hint exists for are still free: no "
      "cost, no hours, no years, no risk",
      len(_fp_free) >= 8, sorted(_fp_free))
# effective_risk is the one true answer (projects.py's own docstring, and
# the reason this must live nowhere else): exercise it directly rather than
# rolling dice, the same style as the retry-learning check just above it.
_s_ctl = sim(capital=10 ** 9)
_bare = NODES["zone_refining"]["risk"]
check("with no process controller built, a process_control node's "
      "effective_risk is untouched - relief is earned, not ambient",
      _s_ctl.effective_risk("zone_refining") == _bare,
      _s_ctl.effective_risk("zone_refining"))
_s_ctl.done.add("ctl_pneumatic_process_controller")
_ctl_relieved = _s_ctl.effective_risk("zone_refining")
check("building the controller cuts a 45% node to a real, still-substantial "
      "chance of failure - meaningfully survivable, not a formality: down "
      "by CONTROL_RELIEF_FACTOR (35%), to about 0.29, not to zero and not "
      "to a rounding error",
      abs(_ctl_relieved - _bare * _s_ctl.CONTROL_RELIEF_FACTOR) < 1e-9
      and 0.20 < _ctl_relieved < 0.35,
      _ctl_relieved)
_bare_other = NODES["screw_lathe"]["risk"]
check("the SAME controller gives no relief at all to a node that was never "
      "tagged process_control - screw_lathe's risk is a one-shot mechanical "
      "build, not a held process, and the relief must not leak onto it",
      _s_ctl.effective_risk("screw_lathe") == _bare_other,
      _s_ctl.effective_risk("screw_lathe"))
for _m in range(4):
    _s_ctl.failed_attempts["zone_refining"] = _m
    _s_ctl.learn_from_failed_attempt("zone_refining")
check("relief and learning from failures multiply together rather than one "
      "overriding the other, and the combination still never reaches zero "
      "- floored by RISK_SHARE_AT_FULL_DEPTH times CONTROL_RELIEF_FACTOR times the "
      "bare risk, comfortably above nothing",
      _s_ctl.effective_risk("zone_refining")
      >= _bare * RISK_SHARE_AT_FULL_DEPTH * _s_ctl.CONTROL_RELIEF_FACTOR - 1e-9
      and _s_ctl.effective_risk("zone_refining") < _ctl_relieved,
      _s_ctl.effective_risk("zone_refining"))
_s_ctl.failed_attempts["zone_refining"] = 0
_s_ctl.state.projects.tenure.clear()
