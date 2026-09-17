"""scanners_and_scheduling: split verbatim from the old test_regressions.py (original lines 11086-12865).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# A GENERIC FOG SCANNER. `bounty` leaked three hidden node ids (power_grid,
# an induction-coupling prerequisite, a hidden cathode) before anyone wrote
# a test pinned to that one command by name - because the fog filter lived
# in start_reason alone and nothing stopped a second command from building
# its own unfiltered prerequisite list. This scans EVERY command in
# KNOWN_COMMANDS at once, generically, so the NEXT command to do that -
# including `capacity`, `economy` and `changes`, built this round - is
# caught here rather than found by a playtester.
# =============================================================================
_fogscan = sim(capital=5_000_000.0)
_fogscan.fog = True
_fogscan.revealed = set()
_fogscan_visible = sorted(k for k in NODES if _fogscan.is_visible(k))
_fogscan_goal = _fogscan.goal
_fogscan_hidden = {k for k in NODES
                   if k not in _fogscan_visible and k != _fogscan_goal}
check("a fresh fogged founder has both a visible node and a large hidden "
      "remainder to test against - a property of the live tree, not an "
      "invented fixture",
      bool(_fogscan_visible) and len(_fogscan_hidden) > 1000,
      (len(_fogscan_visible), len(_fogscan_hidden)))
_fv = _fogscan_visible[0]
_fogscan_args = {
    "why": {"id": _fv}, "path": {"id": _fv},
    "start": {"id": "__no_such_node__"}, "stop": {"id": "__no_such_node__"},
    "bounty": {"id": _fv}, "mothball": {"id": "__no_such_node__"},
    "restore": {"id": "__no_such_node__"}, "open": {"id": _fv},
    "buy": {"what": "mine", "material": "iron", "n": 1},
    "quote": {"what": "mine", "material": "iron", "n": 1},
    "close": {"what": "iron", "material": "iron"},
    "hire": {"trade": "smith", "n": 1}, "fire": {"trade": "smith", "n": 1},
    "train": {"trade": "smith", "n": 1}, "work": {"trade": "smith", "hours": 10},
    "commission": {"trade": "smith", "hours": 10}, "bribe": {"amount": 10},
    "changes": {"years": 5}, "policy": {},
}
# save/load/quit: side effects (a file written, the run ended) unrelated to
# what this test is about, and excluded for that reason, not for safety.
_fogscan_skip = {"save", "load", "quit"}
_word_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_fogscan_leaks = {}
for _c in S.KNOWN_COMMANDS:
    if _c in _fogscan_skip:
        continue
    _obj = dict(_fogscan_args.get(_c, {}))
    _obj["cmd"] = _c
    try:
        _resp = S._agent_dispatch(_fogscan, NODES, _obj)
    except Exception as _e:
        continue   # a crash is a different bug; this test is only about leaks
    _tokens = set(_word_re.findall(json.dumps(_resp)))
    _leaked = sorted(_fogscan_hidden & _tokens)
    if _leaked:
        _fogscan_leaks[_c] = _leaked[:5]
check("no command in KNOWN_COMMANDS prints the raw id of a node this fogged "
      "founder has never heard of - scanned generically across every "
      "command at once, so the next command to grow this bug is caught "
      "here rather than by a playtester, the way `bounty` was",
      not _fogscan_leaks, _fogscan_leaks)

# =============================================================================
# A GENERIC COMMAND-POINTER SCANNER. `state`'s own footer once pointed a
# player at `training_pending` with nothing behind it - "did you mean: "
# answered with a command that does not exist - and the fix for that one
# name would not have caught the next one. This walks every reply
# KNOWN_COMMANDS and help can produce, collects every "{"cmd":"X"}" and
# "see 'X'" pointer found anywhere in them, and asserts X is something
# the parser - parse_typed's own KNOWN_COMMANDS/TYPED_ALIASES check -
# actually accepts. Generic across every command at once, the same shape
# as the fog scanner above, so the next stale pointer is caught here.
# =============================================================================
from engine.protocol import TYPED_ALIASES as _TYPED_ALIASES


def _strings_of(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings_of(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _strings_of(v)


_ptr_sim = sim(capital=5_000_000.0)
_ptr_strings = []
for _pc in S.KNOWN_COMMANDS:
    if _pc in ("save", "load", "quit", "step"):
        continue            # side effects unrelated to what this scans for
    _pobj = dict(_fogscan_args.get(_pc, {}))
    _pobj["cmd"] = _pc
    try:
        _pr = S._agent_dispatch(_ptr_sim, NODES, _pobj)
    except Exception:
        continue             # a crash is a different bug
    _ptr_strings.extend(_strings_of(_pr))
for _pt in list(S.HELP_TOPICS) + [None]:
    _ptr_strings.extend(_strings_of(S._agent_help(_ptr_sim, _pt)))
_ptr_cmd_re = re.compile(r'\{"cmd":"([A-Za-z_]+)"')
_ptr_see_re = re.compile(r"see '([A-Za-z_]+)")
_ptr_found = set()
for _ps in _ptr_strings:
    _ptr_found.update(_ptr_cmd_re.findall(_ps))
    _ptr_found.update(_ptr_see_re.findall(_ps))
_ptr_accepted = set(S.KNOWN_COMMANDS) | set(_TYPED_ALIASES.keys())
_ptr_bad = sorted(_ptr_found - _ptr_accepted)
check("every command every reply in KNOWN_COMMANDS or help points a player "
      "at - every {\"cmd\":\"X\"} and every bare see 'X' - is a command the "
      "parser actually accepts, walked generically so the class of bug "
      "`training_pending` was (advertised, not implemented) cannot come "
      "back under a different name",
      not _ptr_bad, (_ptr_bad, sorted(_ptr_found)))
check("...and the scan actually found real pointers to check - an empty "
      "result from a broken scanner would pass this test for the wrong "
      "reason",
      len(_ptr_found) >= 10, sorted(_ptr_found))

# --- a failed attempt teaches you something (projects.py: retry learning) ---
# A player who had already won the game: a failed high-pressure steam system
# used to reset the calendar floor to zero and roll again at the identical
# probability, as if the first attempt had never happened. Now failed_attempts
# (counted since before this round, never spent) buys BOTH a smaller chance of
# failing the same way twice and a banked share of the calendar clock - see
# projects.py's own section comment on _complete for the full reasoning.
_s_rl = sim(capital=10 ** 9)
_rl_k = [k for k in NODES if NODES[k]["risk"] >= 0.15][0]
# _retry_risk_multiplier reads failed_attempts off the Sim itself, so the
# cleanest way to check the whole decaying sequence is to walk it forward by
# setting failed_attempts directly rather than actually rolling failures.
_seq = []
for _m in range(5):
    _s_rl.failed_attempts[_rl_k] = _m
    _seq.append(_s_rl.effective_risk(_rl_k))
check("attempt one faces the bare, untrained risk - nothing has been "
      "learned yet because nothing has failed yet",
      _seq[0] == NODES[_rl_k]["risk"], _seq[0])
check("each later attempt's risk is strictly lower than the one before it, "
      "and a fourth attempt (three failures in) is meaningfully better than "
      "the first, not just marginally",
      all(_seq[i] < _seq[i - 1] for i in range(1, 5))
      and _seq[3] <= _seq[0] * 0.75, _seq)
check("...but it is never a guarantee: risk never reaches zero, bounded "
      "below by RETRY_RISK_FLOOR's own share of the bare risk",
      all(s_ >= NODES[_rl_k]["risk"] * _s_rl.RETRY_RISK_FLOOR - 1e-9 for s_ in _seq),
      _seq)
_s_rl.failed_attempts[_rl_k] = 0

class _AlwaysFails(random.Random):
    """0.0 is below every risk the tree defines, so this fails every roll -
    the mirror image of path_search.py's own DetRNG, which returns 1.0 to
    never fail anything."""
    def random(self):
        return 0.0


_s_cal = sim(capital=10 ** 9)
_cal_k = [k for k in NODES if NODES[k]["risk"] >= 0.15 and NODES[k]["yrs"] >= 5][0]
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
      and all(b < _cal_floor for b in _banked), (_banked, _cal_floor))
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
_tl_far = next((r for r in _s_tl.hazard_timeline()
               if r["name"] == "Third century crisis"), None)
_s_tl2 = sim(civ="rome_100ad")
_s_tl2.year = 234
_tl_near = next((r for r in _s_tl2.hazard_timeline()
                 if r["name"] == "Third century crisis"), None)
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
      [r["years_until"] for r in _s_tl.hazard_timeline()]
      == sorted(r["years_until"] for r in _s_tl.hazard_timeline()),
      [r["years_until"] for r in _s_tl.hazard_timeline()])
_rk_tl = S._agent_dispatch(_s_tl, NODES, {"cmd": "risk"})
check("the `risk` command itself carries the compact timeline, not just "
      "the per-kind breakdown",
      isinstance(_rk_tl.get("knowledge_risk", {}).get("timeline"), list)
      and len(_rk_tl["knowledge_risk"]["timeline"]) > 0, _rk_tl.get("knowledge_risk"))

# --- a warning before the door shuts (projects.py: staffing_closure_warnings)
# close_unstaffed_ventures closes a concern the household can no longer
# supervise; reopen_restaffed_ventures (landed separately) already brings it
# back once restaffed. What was still missing: seeing it coming. "Power grid
# supervision is within 5 craftsmen of closure" - a warning, not a third
# automation; nothing here hires, teaches or stops anything on its own.
_s_sw = sim(civ="rome_100ad")
_sw_cands = [k for k in NODES if NODES[k].get("rev", 0) > 0][:30]
_s_sw.done.update(_sw_cands)
_s_sw._done_changed()
_s_sw.artisans, _s_sw.scholars = 40.0, 10.0
for _k in _sw_cands:
    _s_sw.open_venture(_k)
check("comfortably staffed: no staffing warning at all",
      _s_sw.staffing_closure_warnings() == [], _s_sw.staffing_closure_warnings())
_sw_sch_used, _sw_art_used = _s_sw.venture_staff_used()
_s_sw.artisans = _sw_art_used + 3.0   # inside STAFFING_WARNING_BAND (5)
_sw_warn = _s_sw.staffing_closure_warnings()
check("within the band: a warning names a real operating concern and how "
      "many craftsmen stand between here and its closure",
      bool(_sw_warn) and _sw_warn[0]["id"] in _s_sw.operating
      and _sw_warn[0]["of"] == "craftsmen" and _sw_warn[0]["within"] > 0
      and "spare" in _sw_warn[0]["headline"]
      and "closes" in _sw_warn[0]["headline"], _sw_warn)
check("the concern it names is the same one close_unstaffed_ventures would "
      "actually close first (dearest to keep, for what it ties up)",
      _sw_warn and _sw_warn[0]["id"] == sorted(
          [k for k in _s_sw.operating if _s_sw.venture_hands(k)[1] > 0.005
           or _s_sw.venture_hands(k)[0] > 0.005],
          key=lambda k: ((NODES[k]["rev"] - NODES[k]["up"])
                         / max(0.01, _s_sw.venture_hands(k)[1]),
                         -_s_sw.venture_hands(k)[1]))[0],
      _sw_warn)
_sw_before = set(_s_sw.operating)
_s_sw.artisans = _sw_art_used - 2.0    # room exhausted
_sw_warn2 = _s_sw.staffing_closure_warnings()
check("room exhausted: the warning says so plainly rather than quoting a "
      "negative number of craftsmen",
      bool(_sw_warn2) and "next in line to close" in _sw_warn2[0]["headline"],
      _sw_warn2)
check("this is a warning, not a cure: calling it changes nothing about "
      "who is still operating - only close_unstaffed_ventures itself does "
      "the closing, on its own schedule, unchanged by this",
      set(_s_sw.operating) == _sw_before, sorted(_s_sw.operating))

# --- BREAK: an England player hired more staff, watched this warning's own
# number climb 1.3 to 2.3, and read the RISE as the situation getting WORSE
# before working out that bigger means safer - "the 'X is within N
# craftsmen of closure' warning is ambiguous on first read". The fix is the
# wording, not the arithmetic: "spare" reads as safer the more of it there
# is, the same as the no-slack sibling just above ("has no spare craftsmen:
# losing just one more closes it outright"), and never says "within" at all
# any more, which read like a countdown.
_s_sw2 = sim(civ="rome_100ad")
_s_sw2.done.update(_sw_cands)
_s_sw2._done_changed()
_s_sw2.artisans, _s_sw2.scholars = 40.0, 10.0
for _k in _sw_cands:
    _s_sw2.open_venture(_k)
_sw2_sch_used, _sw2_art_used = _s_sw2.venture_staff_used()
_s_sw2.artisans = _sw2_art_used + 1.3
_sw_before_hire = _s_sw2.staffing_closure_warnings()
_room_before = _sw_before_hire[0]["within"] if _sw_before_hire else None
_s_sw2.artisans += 1.0   # hire one more craftsman
_sw_after_hire = _s_sw2.staffing_closure_warnings()
_room_after = _sw_after_hire[0]["within"] if _sw_after_hire else None
check("hiring more staff moves the reported room UP, same as the England "
      "run (1.3 -> 2.3)",
      _room_before is not None and _room_after is not None
      and _room_after > _room_before,
      (_room_before, _room_after))
check("...and the headline itself uses 'spare', which only reads one way "
      "(more is safer) - never the old 'within N ... of closure' phrasing, "
      "which read like a countdown when the number rose",
      _sw_before_hire and "spare" in _sw_before_hire[0]["headline"]
      and "within" not in _sw_before_hire[0]["headline"]
      and "of closure" not in _sw_before_hire[0]["headline"],
      _sw_before_hire and _sw_before_hire[0]["headline"])
# THE HORIZON MENU MUST NOT SELL THE PLANNER'S FLOOR AS A DIFFICULTY CLAIM.
# Challenge's note used to say 400 years was "short of the measured dice-free
# floor ... means playing better than the unlucky-proof plan". True about the
# instrument, false as advice: a player reached the same Rome goal's startable
# point in 334 years under fog, on a second attempt, with the point-contact
# transistor failing six times. DICE_FREE_FLOOR_YEARS stays in the file as a
# measurement of one policy, and the menu a player reads stays out of the
# business of telling them what is reachable, because critical_path already
# tells them that for the goal they actually picked.
from engine import cli as _CLI

_hz_notes = " ".join(n for _k, _l, _y, n in _CLI.HORIZON_MODES).lower()
check("no horizon-mode description quotes the dice-free floor or calls any "
      "setting unreachable",
      not any(w in _hz_notes for w in
              ("dice-free", "unlucky-proof", "1,019", "1019", "451")),
      _hz_notes)
check("the floor table itself is still there, still per-civilisation, and "
      "still the number PATH_SEARCH.md measured",
      _CLI.DICE_FREE_FLOOR_YEARS.get("rome_100ad") == 1019
      and _CLI.DICE_FREE_FLOOR_YEARS.get("han_china_100ad") == 451,
      _CLI.DICE_FREE_FLOOR_YEARS)

# RETRY LEARNING HAS TO SURVIVE A SAVE. failed_attempts drives
# _retry_risk_multiplier and _retry_calendar_retain, and it was not in
# SAVE_FIELDS, so every resume reset the household to "nothing has ever been
# tried". The player who won the game reported repeated 45% failures with "no
# strategic mitigation visible": the mitigation was there and the save
# round-trip was deleting it.
import collections as _coll
from engine import protocol as _PROTO

_fa_path = os.path.join(HERE, "_fa_roundtrip.json")
_s_fa = sim()
_s_fa.failed_attempts["zone_refining"] = 3
_s_fa.shortages["iron"] = 7
_risk_before = _s_fa.effective_risk("zone_refining")
_cal_before = _s_fa._retry_calendar_retain("zone_refining")
_PROTO.save_state(_s_fa, _fa_path)
_s_fa2 = sim()
_PROTO.load_state(_s_fa2, _fa_path)
check("three failures on zone_refining still stand after a save and a "
      "resume, so the next attempt is the 23.8% the learning bought and not "
      "the bare 45%",
      abs(_s_fa2.effective_risk("zone_refining") - _risk_before) < 1e-9
      and abs(_s_fa2.effective_risk("zone_refining") - 0.2383) < 0.001,
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
_fresh = sim()
_accum = {k for k, v in vars(_fresh).items()
          if isinstance(v, (_coll.defaultdict, _coll.Counter))}
_accum |= {k for k, v in vars(_fresh.household).items()
           if isinstance(v, (_coll.defaultdict, _coll.Counter))}
check("every accumulator a fresh Sim carries is either in SAVE_FIELDS or "
      "listed as deliberately unsaved, so the next one added cannot quietly "
      "reset on every resume the way retry learning did",
      _accum <= (set(_PROTO.SAVE_FIELDS) | _NOT_SAVED_ON_PURPOSE),
      sorted(_accum - (set(_PROTO.SAVE_FIELDS) | _NOT_SAVED_ON_PURPOSE)))
# =============================================================================
# THE SCORE AND THE ENDING. A player who had just won asked for a score,
# weighted across seven things, goal-gated ("no score: the goal was not
# reached"), inspectable mid-run, and respectful of fog - plus a short
# achievements list. See engine/protocol.py's own block comment above
# SCORE_WEIGHTS for which field feeds each component and why.
# =============================================================================
from engine.protocol import (score_report as _SCORE, render_score as _RSCORE,
                             SCORE_WEIGHTS as _SW)

check("score is advertised in KNOWN_COMMANDS, the same way capacity/economy/"
      "changes were",
      "score" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)
check("the seven weights sum to exactly 1.0, so the total is a real "
      "percentage, not one that quietly falls short of or past 100%",
      abs(sum(_SW.values()) - 1.0) < 1e-9, _SW)

_sc_win, _, _ = proto([{"cmd": "score"}])
check("`score` is reachable through the real JSON protocol, not only "
      "in-process",
      _sc_win and _sc_win[0].get("ok") and "components" in _sc_win[0],
      _sc_win[0] if _sc_win else None)

# --- THE GATE: no goal, no score, not a number. ---
_s_nogoal = sim()
_s_nogoal.year = _s_nogoal.cfg["start_year"] + _s_nogoal.cfg["horizon_years"]
_rep_nogoal = _SCORE(_s_nogoal, NODES)
check("a run that ends without the goal gets 'no score: the goal was not "
      "reached', not a number",
      _rep_nogoal["total"] is None
      and _rep_nogoal["no_score"] == "the goal was not reached",
      _rep_nogoal["total"])
check("...and the rendered ending screen says so in the same words",
      "no score: the goal was not reached" in _RSCORE(_rep_nogoal),
      _RSCORE(_rep_nogoal))

# --- MID-RUN: inspectable before the goal is reached, clearly provisional,
# and clearly distinguished from the final, ended case above.
_s_mid = sim(capital=1_000_000.0)
_rep_mid = _SCORE(_s_mid, NODES)
check("mid-run, before the goal and before the horizon, `score` still "
      "shows every component - what you are optimising, not only what you "
      "already won",
      _rep_mid["total"] is None and not _rep_mid["goal_reached"]
      and all(c.get("raw") is not None for c in _rep_mid["components"].values()),
      _rep_mid["components"].keys())
check("...and says the goal has not been reached YET, not that it never "
      "will be - the run is still live",
      "yet" in _RSCORE(_rep_mid), _RSCORE(_rep_mid))

# --- FOG: done_count is visible under fog already (state's own
# done_count); the tree's TOTAL size is not, so technology_coverage must
# withhold its normalized value and denominator specifically, the same way
# final_report already withholds the goal's own road total until the run
# ends (see _score_components' own comment on reveal_tree_total).
_s_fog = sim(capital=1_000_000.0)
_s_fog.fog = True
_rep_fogmid = _SCORE(_s_fog, NODES)
_tc_fogmid = _rep_fogmid["components"]["technology_coverage"]
check("under fog, mid-run, technology coverage withholds the tree's total "
      "and its own normalized value",
      _tc_fogmid["normalized"] is None and _tc_fogmid["of_total"] is None
      and _tc_fogmid["raw"] == len(_s_fog.done),
      _tc_fogmid)
check("...but never hides the raw done-count, which `state` already shows "
      "under fog regardless",
      _tc_fogmid["raw"] is not None, _tc_fogmid)
check("...and the rendered screen never prints the tree's total node count "
      "while withheld",
      str(len(NODES)) not in _RSCORE(_rep_fogmid), _RSCORE(_rep_fogmid))
_s_fog_end = sim(capital=1_000_000.0)
_s_fog_end.fog = True
_s_fog_end.year = _s_fog_end.cfg["start_year"] + _s_fog_end.cfg["horizon_years"]
_rep_fogend = _SCORE(_s_fog_end, NODES)
_tc_fogend = _rep_fogend["components"]["technology_coverage"]
check("once the run ends, fog lifts exactly this one number - the reward "
      "for finishing, the same reasoning final_report's own road total "
      "already uses",
      _tc_fogend["normalized"] is not None
      and _tc_fogend["of_total"] == len(NODES), _tc_fogend)
_s_nofog = sim(capital=1_000_000.0)
check("off fog, technology coverage is visible immediately, mid-run - fog "
      "is the only thing that ever withholds it",
      _SCORE(_s_nofog, NODES)["components"]["technology_coverage"]["normalized"]
      is not None, None)

# --- THE BUG THIS WORK FOUND: _agent_end_reason's fog branch never checked
# s.goal_year at all, so a player who won under fog and kept building (the
# normal case since reaching the goal stopped being an ending) was told at
# the horizon "you built N things... and did not reach X" about a goal they
# had, in fact, reached.
_s_wonfog = sim(capital=1_000_000.0)
_s_wonfog.fog = True
_s_wonfog.goal_year = _s_wonfog.year + 5
_s_wonfog.year = _s_wonfog.cfg["start_year"] + _s_wonfog.cfg["horizon_years"]
_end_wonfog = S._agent_end_reason(_s_wonfog)
check("BREAK: under fog, a player who reached the goal and kept building "
      "to the horizon is told they reached it, not that they did not",
      "did not reach" not in _end_wonfog and "reached" in _end_wonfog,
      _end_wonfog)
_s_lostfog = sim(capital=1_000_000.0)
_s_lostfog.fog = True
_s_lostfog.year = _s_lostfog.cfg["start_year"] + _s_lostfog.cfg["horizon_years"]
check("...while a player who never reached it under fog still reads the "
      "honest 'did not reach' message, unchanged",
      "did not reach" in S._agent_end_reason(_s_lostfog), None)

# --- ACHIEVEMENTS: each one flips on its own tracked field, in isolation,
# and none of them fire before the goal is reached at all.
def _won_sim(**extra):
    s = sim(capital=5_000_000.0)
    s.goal_year = s.year + 1
    for k, v in extra.items():
        setattr(s, k, v)
    return s

_ach_clean = _SCORE(_won_sim(), NODES)["achievements"]
check("a clean won run earns every achievement this suite can isolate",
      all(a["won"] for name, a in _ach_clean.items()
          if name != "outpaced_the_fastest_plan"),
      _ach_clean)
check("...and a run that never reached the goal earns none at all - no "
      "achievement fires on an unfinished run",
      _SCORE(sim(capital=5_000_000.0), NODES)["achievements"] == {},
      _SCORE(sim(capital=5_000_000.0), NODES)["achievements"])

_ach_sack = _SCORE(_won_sim(forgotten={"corpus_written": 300}), NODES)["achievements"]
check("BREAK-style isolation: a sacking that forgot even one technology "
      "costs only the corpus achievement, not the others",
      not _ach_sack["corpus_intact"]["won"]
      and _ach_sack["never_understaffed"]["won"]
      and _ach_sack["free_hands_only"]["won"], _ach_sack)

_ach_staff = _SCORE(_won_sim(shut_for_staff={"workshop_first": 150}),
                    NODES)["achievements"]
check("...a concern once closed for want of staff costs only that "
      "achievement",
      not _ach_staff["never_understaffed"]["won"]
      and _ach_staff["corpus_intact"]["won"], _ach_staff)

_ach_debt = _SCORE(_won_sim(insolvent_years=1), NODES)["achievements"]
check("...one insolvent year costs the clean-ledger achievement",
      not _ach_debt["clean_ledger"]["won"]
      and _ach_debt["corpus_intact"]["won"], _ach_debt)
_ach_interest = _SCORE(_won_sim(interest_paid=0.01), NODES)["achievements"]
check("...and so does a single denarius of interest paid, on its own",
      not _ach_interest["clean_ledger"]["won"], _ach_interest)

_ach_slave = _SCORE(_won_sim(slaves=1), NODES)["achievements"]
check("...owning even one slave costs only the free-hands achievement",
      not _ach_slave["free_hands_only"]["won"]
      and _ach_slave["clean_ledger"]["won"], _ach_slave)

_s_fast = sim(capital=5_000_000.0)
_s_fast.goal_year = _s_fast.cfg["start_year"] + 1
_ach_fast = _SCORE(_s_fast, NODES)["achievements"]
check("reaching the goal almost immediately outpaces twice its own "
      "critical-path floor",
      _ach_fast["outpaced_the_fastest_plan"]["won"], _ach_fast)
_s_slow = sim(capital=5_000_000.0)
_s_slow.goal_year = _s_slow.cfg["start_year"] + 5000
_ach_slow = _SCORE(_s_slow, NODES)["achievements"]
check("...while dawdling to five thousand years after the start does not",
      not _ach_slow["outpaced_the_fastest_plan"]["won"], _ach_slow)

# --- DETERMINISM: institutions sums floats over CAPABILITY_INSTITUTIONS, a
# frozenset, so this has to be proven under a different PYTHONHASHSEED, the
# same way the rest of this suite proves determinism elsewhere (see the
# literacy/trade-absorption check just above this section's own kin).
def _score_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "from engine.protocol import score_report as SC; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=False, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':5000000.0}); "
         "s.goal, s.done_year = T['meta']['goal_node'], {}; "
         "s.goal_year = s.year + 1; "
         "[s.done.add(k) for k in sorted(s.CAPABILITY_INSTITUTIONS)]; "
         "[s.operating.add(k) for k in sorted(s.CAPABILITY_INSTITUTIONS)]; "
         "s.inst_units = {k: 2.0 for k in s.SCALABLE_INSTITUTIONS}; "
         "s._done_changed(); "
         "r = SC(s, N); "
         "print(repr((round(r['components']['institutions']['normalized'], 12), "
         "r['total'])))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_score_seed_a, _score_seed_b = _par_map(_score_snapshot, ("0", "98765"))
check("the institutions component, and the total it feeds, are identical "
      "under a different PYTHONHASHSEED",
      _score_seed_a == _score_seed_b and _score_seed_a,
      (_score_seed_a, _score_seed_b))

# --- THE ENDING SCREEN carries the score, rendered, not a second report a
# player has to go ask for separately.
_s_endsc = sim(capital=5_000_000.0)
_s_endsc.goal_year = _s_endsc.year + 1
_s_endsc.year = _s_endsc.cfg["start_year"] + _s_endsc.cfg["horizon_years"]
_final_sc = _FRPT(_s_endsc, NODES)
check("the ending screen's final_report carries the score, not just the "
      "road-to-the-goal tally it already had",
      _final_sc.get("score", {}).get("total") is not None, _final_sc.get("score"))
check("...and renders as part of the same page, not a separate dump",
      "SCORE" in _RF(_final_sc) and "TOTAL:" in _RF(_final_sc), _RF(_final_sc)[:200])

# --- POINTS: a number to compare runs with, alongside the percentage, not
# instead of it - and still the same capped total, just rescaled.
check("a won run's score carries a points figure beside the percentage",
      _final_sc["score"].get("points") is not None, _final_sc["score"])
check("points is a lossless, exact rescaling of the SAME capped total - "
      "1000 for a perfect run - never a second figure computed some other "
      "way that could disagree with the percentage",
      _final_sc["score"]["points"] == round(_final_sc["score"]["total"] * 1000),
      (_final_sc["score"]["points"], _final_sc["score"]["total"]))
check("...and it is printed on the rendered score screen too, not only in "
      "the JSON a script would read",
      "1000 points" in _RF(_final_sc) or "/ 1000" in _RF(_final_sc),
      _RF(_final_sc)[:400])
check("a run with no score at all (goal never reached) has no points "
      "either - nothing invented to fill a number in",
      _rep_nogoal.get("points") is None, _rep_nogoal.get("points"))
# PERFECT SCORE NEVER EXCEEDS 1000. Every component clamps its own
# normalized figure to [0, 1] before SCORE_WEIGHTS (which sum to exactly
# 1.0 - checked above) are applied, so there is no way to push `total`
# past 1.0 and no way to push `points` past 1000 - confirmed directly
# against a household built to max out every component at once, not just
# argued from the formula.
_s_perfect = sim(capital=5_000_000.0)
_s_perfect.goal_year = _s_perfect.year + 1
_s_perfect.reputation = 1e9
_s_perfect.scandal = -1e9
_s_perfect.done = set(NODES)
_s_perfect._done_changed()
_s_perfect.inst_units = {k: 1e9 for k in _s_perfect.SCALABLE_INSTITUTIONS}
for _cik in _s_perfect.CAPABILITY_INSTITUTIONS:
    _s_perfect.operating.add(_cik)
_rep_perfect = _SCORE(_s_perfect, NODES)
check("even a household built to overdrive every single component at "
      "once cannot push the percentage past 100% or the points past 1000",
      _rep_perfect["total"] <= 1.0 + 1e-9
      and _rep_perfect["points"] <= 1000,
      (_rep_perfect["total"], _rep_perfect["points"]))

# --- the missing case: a concern with NO slack at all, where losing one
# more person of its trade closes it outright - not just "within N of
# closure" but the recurring income at stake and the command that fixes it.
_s_sw.artisans = _sw_art_used - 0.6   # room under 1.0: one loss closes it
_sw_warn3 = _s_sw.staffing_closure_warnings()
check("no slack at all: the warning says losing just one more closes it, "
      "not merely that it is 'within' some number",
      bool(_sw_warn3) and _sw_warn3[0]["one_loss_closes_it"]
      and "losing just one more closes it" in _sw_warn3[0]["headline"],
      _sw_warn3)
check("...and names what that closure would actually cost in recurring "
      "income, not just that it would happen",
      _sw_warn3 and _sw_warn3[0]["recurring_income_at_risk"] > 0
      and "den/yr" in _sw_warn3[0]["headline"], _sw_warn3)
check("...and names the command that fixes it - a real {\"cmd\":\"hire\"} "
      "example with a real trade, not just the generic 'craftsmen'/"
      "'scholars' word",
      _sw_warn3 and '"cmd":"hire"' in _sw_warn3[0]["fix"]
      and _sw_warn3[0]["fix"] in _sw_warn3[0]["headline"], _sw_warn3)
check("within the band but NOT down to the last one: one_loss_closes_it is "
      "false, and the headline stays the earlier 'N spare' sentence",
      _sw_warn and _sw_warn[0]["one_loss_closes_it"] is False
      and "spare" in _sw_warn[0]["headline"], _sw_warn)
check("room already exhausted (<=0.05): also costed and fixed, same as the "
      "one-loss-away case",
      _sw_warn2 and _sw_warn2[0]["recurring_income_at_risk"] > 0
      and '"cmd":"hire"' in _sw_warn2[0]["fix"], _sw_warn2)
# render_state used to crash the instant any staffing warning fired at all -
# "can only concatenate str (not 'dict') to str" - because
# staffing_closure_warnings() returns dicts and the renderer assumed bare
# strings. Nothing caught this because the regression suite only ever called
# the engine method directly, never through the human-text renderer.
_sw_state_out = S._agent_dispatch(_s_sw, NODES, {"cmd": "state"})
check("render_state no longer crashes when a staffing warning is live, and "
      "prints the actual headline sentence",
      _sw_warn3[0]["name"] in _RSTATE(_sw_state_out), _sw_state_out.get("supervision_close_to_the_edge"))

# ======================================================================
# ROUND 9: expected calendar cost of a risky node, including retries
# (projects.py: calendar_floor, expected_calendar_years). A 45%-risk,
# 4-year-floor node is not a 4-year project - the raw geometric series
# 1/(1-p) says 1.82 attempts, and even that is wrong once retry learning
# (RETRY_RISK_FLOOR, RETRY_CALENDAR_CAP) starts changing the odds and the
# wait on every attempt after the first. Verified both in closed form and,
# separately in a throwaway Monte Carlo harness during development, against
# thousands of real _complete() calls - see the session's own report for
# those numbers; what is pinned here is the cheap, deterministic shape of
# the guarantee, not a re-run of the simulation on every gate pass.
# ======================================================================
_s_ey = sim(civ="rome_100ad")
_riskfree = next(k for k in NODES if NODES[k].get("risk", 1) == 0)
check("risk-free node: expected calendar years is exactly the bare floor - "
      "there is nothing to retry",
      abs(_s_ey.expected_calendar_years(_riskfree)
          - _s_ey.calendar_floor(_riskfree)) < 1e-9,
      (_riskfree, _s_ey.expected_calendar_years(_riskfree),
       _s_ey.calendar_floor(_riskfree)))
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
# instead hard-codes RETRY_RISK_FLOOR/DECAY would pass today and go on
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
_s_ey2 = sim(civ="rome_100ad")
_s_ey2.failed_attempts["point_contact_transistor"] = 3
check("...concretely: 3 prior failures leaves less EXPECTED remaining "
      "calendar time than attempt one alone faced, not more",
      _s_ey2.expected_calendar_years("point_contact_transistor") < _pct_exp,
      (_s_ey2.expected_calendar_years("point_contact_transistor"), _pct_exp))
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
_s_ey3 = sim(civ="rome_100ad", capital=10_000_000.0)
for _p in NODES["point_contact_transistor"]["pre"]:
    _s_ey3.done.add(_p)
_s_ey3._done_changed()
_s_ey3.scholars, _s_ey3.artisans = 200.0, 200.0
_s_ey3.trades_created.update(["chemist", "machinist"])
_s_ey3.employees["chemist"], _s_ey3.employees["machinist"] = 20.0, 20.0
_avail_pct = S._agent_dispatch(_s_ey3, NODES, {"cmd": "available", "find": "point_contact_transistor"})
_avail_rows = _avail_pct.get("available")
_avail_row = next((r for r in _avail_rows if r.get("id") == "point_contact_transistor"), None) \
    if isinstance(_avail_rows, list) else None
check("`available` carries the same expected-years figure on the row, not "
      "only on `why`",
      _avail_row is not None
      and _avail_row.get("expected_calendar_years_with_retries") is not None,
      (_avail_rows, _avail_row))
_s_ey4 = sim(civ="rome_100ad", capital=10_000_000.0)
for _p in NODES["point_contact_transistor"]["pre"]:
    _s_ey4.done.add(_p)
_s_ey4._done_changed()
_s_ey4.scholars, _s_ey4.artisans = 200.0, 200.0
_s_ey4.trades_created.update(["chemist", "machinist"])
_s_ey4.employees["chemist"], _s_ey4.employees["machinist"] = 20.0, 20.0
_start_pct = S._agent_dispatch(_s_ey4, NODES, {"cmd": "start", "id": "point_contact_transistor"})
check("the `start` confirmation carries the expected-years figure too, so "
      "the honest number is in front of the player at the one moment they "
      "are actually committing",
      _start_pct.get("ok") and _start_pct.get("expected_calendar_years_with_retries") is not None,
      _start_pct)

# ======================================================================
# ROUND 10: discoverability - `help commands` and `log`, pointed at
# directly rather than left to be found inside a buried topic list, and
# said ONCE early in a run rather than spammed every turn.
# ======================================================================
_s_hc = sim(civ="rome_100ad")
_help_front = S._agent_dispatch(_s_hc, NODES, {"cmd": "help"})["help"]
check("the no-topic help screen names `help commands` and `log` outright, "
      "not only inside the 'more topics' map a player has to already "
      "suspect exists",
      any("help" in str(k).lower() or "log" in str(v).lower()
          for k, v in _help_front.items()
          if "command index" in str(k).lower() or "exact history" in str(k).lower()),
      list(_help_front.keys()))
check("...and the text itself actually says 'help' topic 'commands' and "
      "mentions log/values/money/automation/save-load, so a reader does not "
      "have to guess what 'the complete command index' contains",
      any("\"topic\":\"commands\"" in str(v) and "log" in str(v)
          for v in _help_front.values()),
      [v for v in _help_front.values() if "\"topic\":\"commands\"" in str(v)])
_s_wk = sim(civ="rome_100ad")
_st1 = S._agent_dispatch(_s_wk, NODES, {"cmd": "state"})
check("a fresh game's very first `state` points at `help commands` and "
      "`log` directly, in the reply itself - not only in the one-time "
      "stderr welcome banner a player could have missed",
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
_s_wk_late = sim(civ="rome_100ad")
_s_wk_late.year = _s_wk_late.cfg["start_year"] + 50
_st_late = S._agent_dispatch(_s_wk_late, NODES, {"cmd": "state"})
check("resuming deep into an existing run (year far past the opening) never "
      "springs this first-timer tip on a player who has long since found "
      "all of this themselves",
      _st_late.get("worth_knowing_early") is None, _st_late.get("worth_knowing_early"))
check("it shows up in the rendered text too, right where the staffing "
      "warning and the idle-hours warning already print",
      "help" in _RSTATE(_st1) and "log" in _RSTATE(_st1), None)

# ======================================================================
# ROUND 11: point_contact_transistor vs single_crystal/silicon_path - the
# specific contradiction a player flagged as still live ("the actual start
# check still requires a semiconductor supplied by single_crystal or
# silicon_path"). Verified against the live tree and the live engine: the
# node's own req_any is empty and its only semiconductor prerequisite is
# ge_reduction. The stale requirement has been removed from the live data and
# start checks.
# ======================================================================
check("point_contact_transistor's req_any is empty - nothing substitutes "
      "single_crystal or silicon_path in for it",
      NODES["point_contact_transistor"]["req_any"] == [], NODES["point_contact_transistor"]["req_any"])
check("...and neither single_crystal nor silicon_path appears anywhere in "
      "its hard prerequisites either",
      "single_crystal" not in NODES["point_contact_transistor"]["pre"]
      and "silicon_path" not in NODES["point_contact_transistor"]["pre"],
      NODES["point_contact_transistor"]["pre"])
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
check("junction_transistor, by contrast, genuinely does need single_crystal "
      "- that gate is real and correctly placed one node further on, not "
      "removed along with point_contact_transistor's stale one",
      "single_crystal" in NODES["junction_transistor"]["pre"], NODES["junction_transistor"]["pre"])

# A FREE PREREQUISITE SHOULD SAY IT IS FREE. Eight cap_* nodes cost nothing,
# take no time and cannot fail, and a player still has to start each by hand.
# The player who won this game called the refusal that names one of them
# "administrative": it said "missing prerequisites: cap_measure_temp" and
# nothing about the thing behind that name being one free command away. They
# are not auto-granted, because each carries 20 a year of upkeep if it is ever
# opened and that is the player's decision to make, and they never need
# opening to satisfy a prerequisite (start_reason tests `p not in self.done`).
_s_fp = sim()
_s_fp.done.add("thermometer"); _s_fp._done_changed()
_, _fp_why = _s_fp.start_reason("chm_crystallisation")
check("a refusal whose missing prerequisite is free, instant and startable "
      "now says so and gives the command, instead of naming it and stopping",
      "costs nothing, takes no time and cannot fail" in (_fp_why or "")
      and "start cap_measure_temp" in (_fp_why or ""), _fp_why)

_s_fp2 = sim()          # thermometer NOT done, so cap_measure_temp is blocked
_, _fp_why2 = _s_fp2.start_reason("chm_crystallisation")
check("...and stays quiet about a free node that is itself blocked, which "
      "would be a second refusal wearing the first one's clothes",
      "costs nothing" not in (_fp_why2 or ""), _fp_why2)

_, _fp_why3 = sim().start_reason("junction_transistor")
check("an ordinary expensive prerequisite gets no such hint",
      "costs nothing" not in (_fp_why3 or ""), _fp_why3)

# UNDER FOG IT MAY NOT NAME WHAT THE PLAYER CANNOT SEE. The hint is built from
# the same `known` list the fog filter already produced, so this is a check
# that it stays built from it.
_s_fpf = sim()
_s_fpf.fog = True
_s_fpf.revealed = set()
_s_fpf.done.add("thermometer"); _s_fpf._done_changed()
_fp_hidden = [k for k in ("cap_measure_temp", "cap_measure_elec",
                          "cap_power_water", "cap_power_steam")
              if not _s_fpf.is_visible(k)]
_fp_msgs = []
for _k in sorted(NODES):
    if any(h in NODES[_k]["pre"] for h in _fp_hidden):
        _, _w = _s_fpf.start_reason(_k)
        if _w:
            _fp_msgs.append(_w)
check("under fog the free-prerequisite hint never names a capability the "
      "player has not heard of",
      bool(_fp_hidden) and not any(h in m for m in _fp_msgs for h in _fp_hidden),
      (_fp_hidden, _fp_msgs[:2]))

# AND THE PREMISE. If one of these ever acquires a cost, the sentence above
# stops being true, so the set it describes has to stay genuinely free.
_fp_free = [k for k, n in NODES.items()
            if k.startswith("cap_") and (n.get("_total_cost") or 0) <= 1
            and (n.get("ph") or 0) == 0 and (n.get("yrs") or 0) == 0
            and (n.get("risk") or 0) == 0]
check("the free capability nodes the hint exists for are still free: no "
      "cost, no hours, no years, no risk",
      len(_fp_free) >= 8, sorted(_fp_free))
# =============================================================================
# PROJECT SCHEDULING, MADE LEGIBLE. A player who had already won the game
# raised this in four separate places across a 500-year run: founder-hours
# reported as free while a cheap project crawled because of the active
# portfolio; one workshop stuck at 60% for a year with no visible cause;
# "waiting on your hours" hard to reconcile with the displayed free hours;
# and trade-hour demand from a shrunk staff competing invisibly across a
# dozen projects. Five things below, one per deliverable.
# =============================================================================
from engine.protocol import _agent_portfolio as _APORT, render_portfolio as _RPORT

# --- 1. PER-PROJECT ALLOCATION, READ FROM THE ALLOCATOR ITSELF. core.py's
# step() (5. progress) now writes pool_total/rank/active_count/remaining_
# before onto each active project's own st dict AS IT DECIDES each one's
# share, and _agent_state/`portfolio` read those fields back rather than
# recomputing a share that could disagree with what was actually applied.
# Two founder-hours-only institutions (no hired trade at all, so nothing
# here is about staffing) share one pool: sc2_institution_doctorate started
# second and so sits at the front of `order` - priority #1, offered its
# full 150 hours against the WHOLE 2,000-hour pool; sc2_institution_
# curriculum is priority #2, offered its 120 against what was left AFTER
# the first one's share, 1,850.
_s_alloc = sim(civ="rome_100ad", capital=5_000_000.0)
_s_alloc.done.update({"school_founded", "fin_university",
                      "sc2_institution_examination"})
_s_alloc._done_changed()
_s_alloc.start_project("sc2_institution_curriculum")
_s_alloc.start_project("sc2_institution_doctorate")
_s_alloc.step()
_st_doc = _s_alloc.active["sc2_institution_doctorate"]
_st_cur = _s_alloc.active["sc2_institution_curriculum"]
check("the allocator stores WHY a project got its share: pool total, this "
      "project's rank in the queue, and how many active projects shared "
      "the pool, all on the same st dict step() itself decided from",
      _st_doc["pool_rank_this_year"] == 1 and _st_cur["pool_rank_this_year"] == 2
      and _st_doc["pool_active_count_this_year"] == 2
      and _st_cur["pool_active_count_this_year"] == 2
      and _st_doc["pool_total_this_year"] == 2000.0,
      (_st_doc, _st_cur))
check("the higher-priority project's own share came off the FULL pool, and "
      "the next one in line saw only what was left after it - the exact "
      "arithmetic behind 'this project is receiving N of your M available "
      "directed hours because K active projects are sharing attention'",
      _st_doc["pool_remaining_before_this_year"] == 2000.0
      and _st_cur["pool_remaining_before_this_year"]
      == 2000.0 - _st_doc["hours_offered_this_year"]
      and _st_doc["hours_offered_this_year"] == 150.0
      and _st_cur["hours_offered_this_year"] == 120.0,
      (_st_doc["pool_remaining_before_this_year"],
       _st_cur["pool_remaining_before_this_year"]))
_pf_alloc = S._agent_dispatch(_s_alloc, NODES, {"cmd": "portfolio"})
_pf_rows = {r["id"]: r for r in _pf_alloc["projects"]}
check("`portfolio` prints the SAME numbers the allocator stored - not a "
      "second guess at them: displayed share and applied share can never "
      "differ, because they are read from the identical st dict",
      _pf_rows["sc2_institution_doctorate"]["hours_offered_this_year"]
      == _st_doc["hours_offered_this_year"]
      and _pf_rows["sc2_institution_doctorate"]["hours_effective_this_year"]
      == _st_doc["hours_effective_this_year"]
      and _pf_rows["sc2_institution_doctorate"]["pool_rank_this_year"]
      == _st_doc["pool_rank_this_year"]
      and _pf_rows["sc2_institution_curriculum"]["hours_offered_this_year"]
      == _st_cur["hours_offered_this_year"],
      _pf_rows)
# THE SAME INVARIANT, THROUGH A JSON ROUND-TRIP - what an agent parsing
# `portfolio json` actually receives, not the live Python dict.
_pf_parsed = json.loads(json.dumps(_pf_alloc))
_pf_parsed_rows = {r["id"]: r for r in _pf_parsed["projects"]}
check("the same equality survives a real json.dumps/json.loads round trip",
      _pf_parsed_rows["sc2_institution_doctorate"]["hours_offered_this_year"]
      == _st_doc["hours_offered_this_year"],
      _pf_parsed_rows["sc2_institution_doctorate"])

# --- 2a. PER-TRADE DEMAND VS SUPPLY, AGGREGATED, BEFORE COMMITTING. "With
# only one active chemist remaining after attrition, numerous projects
# reached ~60% founder work but then stalled because their chemist-hours
# were all competing for the same 3,000 annual trade-hours." Six chemist-
# using projects, one shared trade, supply pinned to 1,500 - well under
# what six projects each wanting hundreds of hours would want at once.
_s_dem = sim(civ="rome_100ad", capital=5_000_000.0)
_dem_targets = sorted(k for k in NODES
                      if (NODES[k].get("lab") or {}).get("chemist"))[:6]
for _k in _dem_targets:
    _n = NODES[_k]
    _s_dem.active[_k] = dict(ph_left=float(_n["ph"]), yrs=0.0, spent=0.0,
                             cost_left=_s_dem.project_cost(_k),
                             lab_left=dict(_n["lab"]))
_dem_real_hycco = _s_dem.hours_you_can_call_on
_s_dem.hours_you_can_call_on = (
    lambda t, _r=_dem_real_hycco: 1500.0 if t == "chemist" else _r(t))
# INDEPENDENTLY DERIVED, from trade_draw_plan (the same read-only formula
# lab_year_draw itself uses for the demand side) called once per project -
# not the aggregate function under test - so a break in the aggregation
# loop shows up as a mismatch here.
_expect_demand = sum(
    _s_dem.trade_draw_plan(_k, None).get("chemist", {}).get("desired", 0.0)
    for _k in _dem_targets)
_dvs = _s_dem.trade_demand_vs_supply()
check("trade_demand_vs_supply sums each active project's own read-only "
      "demand for the trade, not a second, independently-guessed total",
      abs(_dvs["chemist"]["demand_hours_this_year"] - _expect_demand) < 0.5,
      (_dvs["chemist"]["demand_hours_this_year"], _expect_demand))
check("...against what the trade can actually supply this year, and flags "
      "the portfolio as oversubscribed on it when demand exceeds supply",
      _dvs["chemist"]["supply_hours_this_year"] == 1500.0
      and _dvs["chemist"]["oversubscribed"] is True
      and _expect_demand > 1500.0, _dvs["chemist"])
check("...and names every project actually drawing on it, so a player can "
      "see which of their own projects are competing, not only that some "
      "of them are",
      set(_dvs["chemist"]["projects_drawing_on_it"]) == set(_dem_targets),
      _dvs["chemist"]["projects_drawing_on_it"])
_port_dem = _APORT(_s_dem, NODES)
_port_dem_row = next(r for r in _port_dem["trade_hours_demand_vs_supply"]
                     if r["trade"] == "chemist")
check("`portfolio`'s own trade-demand table reads the identical numbers, "
      "never a re-derived estimate that could disagree with them",
      _port_dem_row["demand_hours_this_year"]
      == _dvs["chemist"]["demand_hours_this_year"]
      and _port_dem_row["oversubscribed"] == _dvs["chemist"]["oversubscribed"],
      _port_dem_row)

# --- 2b. THE SAME OVERSUBSCRIPTION, VISIBLE AT `start` ITSELF. "The first
# workshop/lab sat at 60% until I stopped adding new work for a year" - a
# player should not have to discover this 60% in. One chemist-needing
# project already active and holding 80 of a pinned 150-hour chemist
# supply; starting a second that alone would fit (100 <= 150) but not
# alongside the first (80 + 100 > 150) must say so AT the moment of
# commitment, not merely let it start silently and crawl.
_s_over = sim(civ="rome_100ad", capital=5_000_000.0)
_s_over.trades_created.add("chemist")
_s_over.employees["chemist"] = 20.0
_s_over._resync_pools()
_over_real_hycco = _s_over.hours_you_can_call_on
_s_over.hours_you_can_call_on = (
    lambda t, _r=_over_real_hycco: 150.0 if t == "chemist" else _r(t))
_ok_over, _why_over = _s_over.start_project("md2_local_anaesthesia")
check("(setup) the first chemist-needing project starts cleanly on its own",
      _ok_over, _why_over)
_resp_over = S._agent_dispatch(_s_over, NODES,
                               {"cmd": "start", "id": "md2_staining_methylene"})
check("a `start` that would oversubscribe a trade says so in the "
      "confirmation itself, naming the trade, the portfolio's new total "
      "demand and what the trade can actually supply",
      _resp_over.get("ok") is True
      and "chemist" in (_resp_over.get("this_oversubscribes_a_trade") or "")
      and "180" in _resp_over["this_oversubscribes_a_trade"]
      and "150" in _resp_over["this_oversubscribes_a_trade"],
      _resp_over.get("this_oversubscribes_a_trade"))
check("...and it does not block the start - overcommitting is still the "
      "player's call, only an informed one now",
      "md2_staining_methylene" in _s_over.active, sorted(_s_over.active))

# --- 3. FIVE PRECISE REASONS, NOT A BLURRED "NOBODY TO DO THE WORK". The
# weak spot the player named was specifically the labour cases: an absolute
# staffing shortage and a trade your OWN other work has booked used to
# share one label and one remedy-less sentence.
from engine.protocol import _portfolio_constraint as _PCON
_s_staff = sim(civ="rome_100ad", capital=1e9)
_staff_k = next(k for k in NODES if (NODES[k].get("lab") or {}).get("chemist"))
_n_staff = NODES[_staff_k]
_s_staff.active[_staff_k] = dict(ph_left=float(_n_staff["ph"]), yrs=0.0,
                                 spent=0.0, cost_left=_s_staff.project_cost(_staff_k),
                                 lab_left=dict(_n_staff["lab"]))
_w_staff = _WO(_s_staff, NODES, _staff_k, _s_staff.active[_staff_k],
              _s_staff.active[_staff_k]["cost_left"])
check("an ABSOLUTE staffing shortage (this society can field none of the "
      "trade at all) is its own precise reason",
      _w_staff.startswith("nobody to do the work") and _PCON(_w_staff) == "staffing",
      _w_staff)

_s_book = sim(civ="rome_100ad", capital=1e9)
_s_book.trades_created.add("chemist")
_s_book.employees["chemist"] = 0.8
_s_book._resync_pools()
_n_book = NODES[_staff_k]
_s_book.active[_staff_k] = dict(ph_left=float(_n_book["ph"]), yrs=0.0,
                                spent=0.0, cost_left=_s_book.project_cost(_staff_k),
                                lab_left=dict(_n_book["lab"]))
# A real competing project, so the portfolio view and the per-project reason
# are testing the same allocation data rather than an invented used-hours
# counter that could equally have been this project's own successful draw.
_other_book = next(k for k in NODES
                   if k != _staff_k and (NODES[k].get("lab") or {}).get("chemist")
                   and (NODES[k]["lab"]["chemist"] / max(1.0, NODES[k]["yrs"])
                        + NODES[_staff_k]["lab"]["chemist"]
                        / max(1.0, NODES[_staff_k]["yrs"])
                        > _s_book.hours_you_can_call_on("chemist")))
_n_other_book = NODES[_other_book]
_s_book.active[_other_book] = dict(
    ph_left=float(_n_other_book["ph"]), yrs=0.0, spent=0.0,
    cost_left=_s_book.project_cost(_other_book),
    lab_left=dict(_n_other_book["lab"]))
_w_book = _WO(_s_book, NODES, _staff_k, _s_book.active[_staff_k],
             _s_book.active[_staff_k]["cost_left"])
check("a trade your OWN other active work has already booked - the society "
      "CAN field it - is a DIFFERENT, distinctly-worded reason with a "
      "different remedy (stop something else, do not go hire or teach)",
      _w_book.startswith("trade hours already booked") and _PCON(_w_book) == "trade_hours"
      and _w_book != _w_staff, _w_book)

_s_mat = sim(civ="rome_100ad", capital=1e9)
_s_mat.active["gunpowder"] = dict(
    ph_left=float(NODES["gunpowder"]["ph"]), yrs=0.0, spent=0.0,
    cost_left=_s_mat.project_cost("gunpowder"), lab_left=dict(NODES["gunpowder"]["lab"]))
_w_mat = _WO(_s_mat, NODES, "gunpowder", _s_mat.active["gunpowder"],
            _s_mat.active["gunpowder"]["cost_left"])
check("a project short of nothing - staff, money, calendar - can still be "
      "waiting on MATERIALS: one economy-wide shortage (here, saltpetre for "
      "gunpowder) scales every project's hours down by the same factor, and "
      "that is now a fifth, distinct, named reason",
      _w_mat.startswith("materials:") and "saltpetre" in _w_mat
      and _PCON(_w_mat) == "materials", _w_mat)
check("calendar and money, the two the player already called clear, are "
      "untouched by any of this",
      _PCON("the calendar") == "calendar"
      and _PCON("money: 40 still owed and this year's instalment of 10 is "
               "more than you can raise") == "money", None)
check("'your hours', enriched with the allocator's own rank/pool figures "
      "(deliverable 1), still classifies as the founder-hours bucket",
      _PCON("your hours") == "founder_hours"
      and _PCON("your hours: priority #1 of 2 active projects sharing "
               "this year's 2,000 directed hours; more") == "founder_hours",
      None)

# --- 4. WARN BEFORE A MULTI-YEAR STEP WASTES HOURS. "Founder-hours do not
# bank. A player can have long calendar-floor projects running, use `step
# 5`, and unintentionally throw away thousands of usable founder-hours if
# they did not fill the portfolio first." Verified against step() itself,
# not assumed: core.py computes `pool` fresh every year from director_pool()
# minus this year's commitments (core.py step(), "4b. start new projects"),
# and nothing on `self` ever carries a leftover balance into the next call -
# it does not partly bank, it does not bank at all, which is exactly the
# player's own assumption, so the warning below says so plainly rather than
# hedging on a partial-banking case that does not exist.
_s_idle = sim(civ="rome_100ad", capital=5_000_000.0)
_s_idle.done.update({"school_founded", "fin_university",
                     "sc2_institution_examination"})
_s_idle._done_changed()
_s_idle.end_year = _s_idle.cfg["start_year"] + _s_idle.cfg["horizon_years"]
_s_idle.start_project("sc2_institution_curriculum")
_s_idle.start_project("sc2_institution_doctorate")
_s_idle.step()
_year_before_multi_step = _s_idle.year
# CAPTURED BEFORE THE STEP RUNS. Once step(years=5) executes it changes the
# pool this year's idle-hours figure was about; the warning has to be
# checked against what the pool was BEFORE any of the five years ran.
_pre_idle_hours = max(0.0, _s_idle.director_pool()
                      - _s_idle.director_hours_committed())
_resp_idle = S._agent_dispatch(_s_idle, NODES, {"cmd": "step", "years": 5})
check("a multi-year step warns, up front, when this year alone already has "
      "substantial founder-hours going to waste and something is genuinely "
      "startable that could use them",
      bool(_resp_idle.get("multi_year_hours_warning"))
      and "founder-hours" in _resp_idle["multi_year_hours_warning"], _resp_idle.get("multi_year_hours_warning"))
check("...names the actual number of hours at stake, read from the same "
      "founder-hours-available figure `state` itself reports, not a second "
      "guess at it",
      "{:,.0f}".format(_pre_idle_hours) in (_resp_idle.get("multi_year_hours_warning") or ""),
      (_pre_idle_hours, _resp_idle.get("multi_year_hours_warning")))
check("...and says plainly that hours do not bank AT ALL, checked against "
      "step()'s own code rather than repeated as an assumption",
      "do not bank" in (_resp_idle.get("multi_year_hours_warning") or ""),
      _resp_idle.get("multi_year_hours_warning"))
check("it warns and proceeds - the years still actually run",
      _resp_idle.get("ok") is True and _resp_idle["year"] > _year_before_multi_step,
      _resp_idle.get("year"))
_s_idle1 = sim(civ="rome_100ad", capital=5_000_000.0)
_s_idle1.done.update({"school_founded", "fin_university",
                      "sc2_institution_examination"})
_s_idle1._done_changed()
_s_idle1.end_year = _s_idle1.cfg["start_year"] + _s_idle1.cfg["horizon_years"]
_s_idle1.start_project("sc2_institution_curriculum")
_s_idle1.start_project("sc2_institution_doctorate")
_s_idle1.step()
_resp_1yr = S._agent_dispatch(_s_idle1, NODES, {"cmd": "step", "years": 1})
check("a single-year step never carries this warning - it exists only to "
      "protect a MULTI-year request from spending the same idle year "
      "more than once unnoticed",
      _resp_1yr.get("multi_year_hours_warning") is None, _resp_1yr)

# --- 5. MACHINE-READABLE OUTPUT MODES. Every player of this game is an AI
# agent parsing text, and several have lost runs to parsing prose that was
# never meant to be a machine interface.
check("'state json'/'portfolio json'/'risk json' are understood by the "
      "typed parser, in any position, alongside their existing modifiers",
      _PT("state json")[0] == {"cmd": "state", "full": False, "json": True}
      and _PT("state full json")[0] == {"cmd": "state", "full": True, "json": True}
      and _PT("portfolio json")[0] == {"cmd": "portfolio", "json": True}
      and _PT("portfolio")[0] == {"cmd": "portfolio", "json": False}
      and _PT("risk json")[0] == {"cmd": "risk", "json": True}
      and _PT("hazards json")[0] == {"cmd": "risk", "json": True},
      (_PT("state json"), _PT("portfolio json"), _PT("risk json")))
# THE JSON MUST NOT BE A FOG BYPASS. Reusing the exact same fogged founder
# and hidden-node set the generic fog scanner above already built: the
# JSON this session would emit for 'state json'/'portfolio json'/'risk
# json' is exactly json.dumps(the same resp dict render_pretty renders), so
# checking it here is checking the one shared source both paths read from.
for _jc in ("state", "portfolio", "risk"):
    _jresp = S._agent_dispatch(_fogscan, NODES, {"cmd": _jc})
    _jtext = json.dumps(_jresp)
    check("'%s json' parses as valid JSON" % _jc,
          json.loads(_jtext) == _jresp, _jtext[:200])
    _jtokens = set(_word_re.findall(_jtext))
    _jleak = sorted(_fogscan_hidden & _jtokens)
    _jprose = _RP(_jc, _jresp)
    _jprose_leak = sorted(_fogscan_hidden & set(_word_re.findall(_jprose)))
    check("a node this fogged founder has never heard of is absent from "
          "'%s'`s JSON exactly as it is absent from its rendered prose "
          "(both read the identical resp dict; the JSON is not a second, "
          "unfiltered path)" % _jc,
          not _jleak and not _jprose_leak,
          (_jleak, _jprose_leak, _jc))

# NO RENDERER MAY CRASH ON A RICH GAME. A player agent reported the readable
# view of `state` and `step 1` vanishing entirely, replaced by "(could not
# render a readable view of this reply: TypeError: can only concatenate str
# (not \"dict\") to str)", once it had several projects running and several
# concerns open. That was render_state appending staffing-warning DICTS as
# bare strings, and it is fixed - but the class is the point: render_pretty
# catches everything on purpose, so a formatter bug costs the formatting and
# never the session, which is exactly why one can sit there unnoticed. The
# suite had only ever called the engine methods directly, never the
# renderers, which is how it survived. So: build a household rich enough to
# populate every optional section, then render every op in the table.
# THE STATE HAS TO ACTUALLY CARRY THE OPTIONAL SECTIONS, or this proves
# nothing. A first version of this check built a busy household, rendered
# everything, passed - and went on passing with the original bug put back,
# because a busy household is not by itself a household whose concerns are
# one artisan from closing, so render_state never reached the line that
# crashed. Mutation-tested since: with the dict appended bare again, the
# `state` entry below reports the apology and this check fails.
_s_rr = sim(capital=400000.0)
_s_rr.end_year = _s_rr.cfg["start_year"] + _s_rr.cfg["horizon_years"]
_rr_cands = [k for k in sorted(NODES) if NODES[k].get("rev", 0) > 0][:30]
_s_rr.done.update(_rr_cands)
_s_rr._done_changed()
_s_rr.artisans, _s_rr.scholars = 40.0, 10.0
for _k in _rr_cands:
    _s_rr.open_venture(_k)
_rr_started = 0
for _k in ORDER:
    if _rr_started >= 6:
        break
    if _s_rr.start_reason(_k)[0]:
        _s_rr.start_project(_k)
        _rr_started += 1
# one craftsman from closing something, which is the state that broke it
_rr_sch_used, _rr_art_used = _s_rr.venture_staff_used()
_s_rr.artisans = _rr_art_used - 0.6
assert _s_rr.staffing_closure_warnings(), \
    "the renderer sweep needs a live staffing warning or it proves nothing"

_rr_cmds = {"state": {"cmd": "state"}, "step": None, "labour": {"cmd": "labour"},
            "money": {"cmd": "money"}, "risk": {"cmd": "risk"},
            "ventures": {"cmd": "ventures"}, "mines": {"cmd": "mines"},
            "stuck": {"cmd": "stuck"}, "log": {"cmd": "log"},
            "values": {"cmd": "values"}, "policy": {"cmd": "policy"},
            "capacity": {"cmd": "capacity"}, "portfolio": {"cmd": "portfolio"},
            "economy": {"cmd": "economy"}, "changes": {"cmd": "changes"},
            "available": {"cmd": "available"}, "score": {"cmd": "score"}}
_rr_broken = []
for _op, _payload in sorted(_rr_cmds.items()):
    if _payload is None:
        continue
    try:
        _resp = S._agent_dispatch(_s_rr, NODES, _payload)
    except Exception as _e:
        _rr_broken.append((_op, "dispatch raised %s: %s" % (type(_e).__name__, _e)))
        continue
    _txt = _PROTO.render_pretty(_op, _resp)
    if "could not render a readable view" in (_txt or ""):
        _rr_broken.append((_op, _txt[:160]))
check("every command's readable view renders on a household with projects "
      "running, concerns open and staffing short - the state a player agent "
      "was in when the whole annual report vanished behind a TypeError",
      not _rr_broken, _rr_broken)

# AND THE ONE THAT ACTUALLY BROKE, through the renderer rather than the engine
# method, on a state where the warning is live.
_rr_state = S._agent_dispatch(_s_rr, NODES, {"cmd": "state"})
_rr_step = _PROTO.render_pretty("step", S._agent_dispatch(_s_rr, NODES,
                                                          {"cmd": "step", "years": 1}))
check("...including `step`, the other command the report named",
      "could not render a readable view" not in (_rr_step or ""), _rr_step[:200])
# --- control theory and operations research: the measured gap a player who
# had completed 2,822 of 2,836 nodes asked for (Maxwell/Routh/Hurwitz/Nyquist/
# Bode/root-locus stability theory; Minorsky/pneumatic/Ziegler-Nichols process
# control; Erlang queueing theory, Dantzig's simplex, Gantt/critical-path
# scheduling), plus the ONE new multiplier in effective_risk it pays for.
_ctl_new_ids = ["ctl_governor_stability_theory", "ctl_routh_criterion",
                "ctl_hurwitz_criterion", "ctl_nyquist_stability_criterion",
                "ctl_bode_plot_margins", "ctl_root_locus",
                "ctl_minorsky_pid_law", "ctl_pneumatic_process_controller",
                "ctl_ziegler_nichols_tuning", "mfg_queueing_theory",
                "mfg_linear_programming_simplex", "mfg_gantt_chart",
                "mfg_critical_path_method"]
check("every new control-theory / operations-research node parsed into the "
      "merged tree under the id the branch file gave it",
      all(k in NODES for k in _ctl_new_ids),
      [k for k in _ctl_new_ids if k not in NODES])
check("Maxwell's 1868 governor paper is cited by name and date, not just "
      "gestured at, and sits behind the SAME centrifugal governor the tree "
      "already lets a player build",
      "Maxwell" in NODES["ctl_governor_stability_theory"]["note"]
      and "1868" in NODES["ctl_governor_stability_theory"]["note"]
      and "en_centrifugal_governor" in NODES["ctl_governor_stability_theory"]["pre"],
      NODES["ctl_governor_stability_theory"]["note"])
check("Nyquist's criterion sits on top of Black's 1927 feedback amplifier "
      "already in the tree (el2_negative_feedback_stability_gain), the exact "
      "'no body of theory that tells you whether a loop will hunt or hold' "
      "gap named against it",
      "el2_negative_feedback_stability_gain"
      in NODES["ctl_nyquist_stability_criterion"]["pre"],
      NODES["ctl_nyquist_stability_criterion"]["pre"])
check("Minorsky 1922 and Ziegler-Nichols 1942 are both cited by name and "
      "date on the process-controller side of the cluster",
      "Minorsky" in NODES["ctl_minorsky_pid_law"]["note"]
      and "1922" in NODES["ctl_minorsky_pid_law"]["note"]
      and "Ziegler" in NODES["ctl_ziegler_nichols_tuning"]["note"]
      and "1942" in NODES["ctl_ziegler_nichols_tuning"]["note"],
      (NODES["ctl_minorsky_pid_law"]["note"],
       NODES["ctl_ziegler_nichols_tuning"]["note"]))
check("Erlang 1909 (queueing) and Dantzig 1947 (simplex) are cited by name "
      "and date, and queueing theory is wired to the telephone exchange the "
      "tree already has, exactly as the brief specified",
      "Erlang" in NODES["mfg_queueing_theory"]["note"]
      and "1909" in NODES["mfg_queueing_theory"]["note"]
      and "com_telephone_manual_exchange" in NODES["mfg_queueing_theory"]["pre"]
      and "Dantzig" in NODES["mfg_linear_programming_simplex"]["note"]
      and "1947" in NODES["mfg_linear_programming_simplex"]["note"],
      (NODES["mfg_queueing_theory"]["note"],
       NODES["mfg_linear_programming_simplex"]["note"]))
check("the critical path method sits next to the SAME production-schedule "
      "neighbourhood (mfg_production_schedule via mfg_gantt_chart) the brief "
      "named as where these belong, not off on their own",
      "mfg_production_schedule" in NODES["mfg_gantt_chart"]["pre"],
      NODES["mfg_gantt_chart"]["pre"])
check("none of the 13 new nodes was inserted as a prerequisite of anything "
      "that already existed - they consume the existing tree, the existing "
      "tree does not consume them, so the goal's closure cannot have moved",
      not any(k in (n.get("pre", []) or [])
              or any(k in gp.get("options", {}) for gp in n.get("req_any", []) or [])
              for i, n in NODES.items() for k in _ctl_new_ids
              if i not in _ctl_new_ids),
      "a pre-existing node references a new one")
check("...and the goal's required closure is still exactly 154 nodes, "
      "unchanged by adding a whole optional side-branch of theory",
      len(S.closure(NODES, GOAL)) == 154, len(S.closure(NODES, GOAL)))

# failure_kind is a property of the NODE, in the tree data, not a list kept
# in the engine - this is what CONTROL_RELIEF_CAPABILITY in projects.py
# actually reads. Pin the exact set so a future edit that silently widens or
# narrows it (the padding failure mode the brief warned about) is caught.
_process_control_ids = {"zone_refining", "single_crystal", "gecl4_purification",
                         "ge_reduction", "lead_chamber", "crucible_steel",
                         "high_temp_furnace", "steam_high_pressure",
                         "electrolysis_industrial"}
_tagged = {k for k, n in NODES.items() if n.get("failure_kind") == "process_control"}
check("exactly the nine continuous hold-at-setpoint processes are tagged "
      "failure_kind=process_control - each one's OWN note already describes "
      "holding a temperature, rate or composition, which is why it was "
      "chosen and nothing else was",
      _tagged == _process_control_ids, sorted(_tagged))
check("none of the 13 new control-theory/operations-research nodes tagged "
      "itself for relief - the controller mitigates OTHER processes' risk, "
      "it does not cheapen its own construction",
      not (_tagged & set(_ctl_new_ids)), _tagged & set(_ctl_new_ids))

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
check("relief and retry-learning multiply together rather than one "
      "overriding the other, and the combination still never reaches zero "
      "- floored by RETRY_RISK_FLOOR times CONTROL_RELIEF_FACTOR times the "
      "bare risk, comfortably above nothing",
      _s_ctl.effective_risk("zone_refining")
      >= _bare * _s_ctl.RETRY_RISK_FLOOR * _s_ctl.CONTROL_RELIEF_FACTOR - 1e-9
      and _s_ctl.effective_risk("zone_refining") < _ctl_relieved,
      _s_ctl.effective_risk("zone_refining"))
_s_ctl.failed_attempts["zone_refining"] = 0
check("RETRY_RISK_FLOOR and RETRY_CALENDAR_CAP, the retry-learning constants "
      "this change was told not to touch, still hold their original values",
      _s_ctl.RETRY_RISK_FLOOR == 0.40 and _s_ctl.RETRY_CALENDAR_CAP == 0.65,
      (_s_ctl.RETRY_RISK_FLOOR, _s_ctl.RETRY_CALENDAR_CAP))

# THE PATRONAGE REFUSAL LEAKED AN ID, AND HANDED OUT A COMMAND THAT WOULD BE
# REFUSED. A naive Mexica player read "get at least a local patron first:
# 'start patron_local'" in `available`, typed exactly that, and was told by
# the same engine one command later: "you have never heard of any such
# thing." Two faults in one line. Under fog it is a free reveal of an
# undiscovered node, which is the third time this exact filter has been
# skipped by a second caller (start_reason had it, `bounty` skipped it, and
# `why` leaked another node's id through its kb path). And the advice is
# worth nothing in any case when the command it names is refused.
_s_pat = sim(civ="mexica_1500")
_s_pat.fog = True
_s_pat.revealed = set()
_pat_wary = None
for _k in sorted(NODES):
    _ok, _w = _s_pat.start_reason(_k)
    if _w and "state is wary" in _w:
        _pat_wary = _w
        break
check("the patronage refusal fires for a fogged Mexica founder at all, so "
      "the rest of these checks are testing something real",
      _pat_wary is not None, _pat_wary)
check("...and does not name patron_local, which this founder has never "
      "heard of and could not start if they tried",
      _pat_wary is not None and "patron_local" not in _pat_wary, _pat_wary)
check("...and still says what is actually wanted, in words rather than an "
      "id, so the refusal remains useful advice",
      _pat_wary is not None and "patron" in _pat_wary
      and "before anyone here will let you begin" in _pat_wary, _pat_wary)

_s_pat2 = sim(civ="mexica_1500")      # no fog: the id IS the useful answer
_pat_wary2 = None
for _k in sorted(NODES):
    _ok, _w = _s_pat2.start_reason(_k)
    if _w and "state is wary" in _w:
        _pat_wary2 = _w
        break
# A REFUSAL MAY NEVER RECOMMEND A REFUSAL. That was the whole complaint, and
# the fog was only half of it: patron_local itself wants identity_cover, so
# even with the fog off "get a local patron first: 'start patron_local'" sent
# the player into "missing prerequisites: identity_cover". So the rule is
# conditional, and both branches are checked: name the command only when it
# would actually be accepted, and otherwise name what is standing in the way.
_pat_can2, _ = _s_pat2.start_reason("patron_local")
check("without fog, the refusal names 'start patron_local' only when that "
      "command would actually be accepted, and otherwise says what "
      "patron_local is itself waiting on",
      (("start patron_local" in _pat_wary2) if _pat_can2
       else ("start patron_local" not in _pat_wary2
             and "itself wants" in _pat_wary2)), (_pat_can2, _pat_wary2))

_s_pat4 = sim(civ="mexica_1500")
_s_pat4.done.add("identity_cover")
_s_pat4._done_changed()
_pat_wary4 = None
for _k in sorted(NODES):
    _ok, _w = _s_pat4.start_reason(_k)
    if _w and "state is wary" in _w:
        _pat_wary4 = _w
        break
_pat_can4, _pat_why4 = _s_pat4.start_reason("patron_local")
check("...and once patron_local IS startable, the refusal hands over the "
      "exact command, and that command is genuinely accepted",
      _pat_can4 and _pat_wary4 is not None
      and "start patron_local" in _pat_wary4, (_pat_why4, _pat_wary4))

# THE SENATORIAL HALF OF THE SAME LINE, which had the identical hardcoded id.
_s_pat3 = sim(civ="rome_100ad")
_s_pat3.fog = True
_s_pat3.revealed = set()
_pat_sen = [_w for _w in
            (_s_pat3.start_reason(_k)[1] for _k in sorted(NODES))
            if _w and "actively opposes" in _w]
check("the senatorial-patronage refusal does not leak its id under fog "
      "either",
      not any("patron_senatorial" in _w for _w in _pat_sen),
      _pat_sen[:1])

# THE POLICY SCREEN GROUPS BY WHAT IS ACTUALLY RUNNING. An England play
# tester read auto_open's description ("opens concerns that plainly pay for
# themselves"), built a pawnshop that plainly paid for itself, watched
# nothing happen, and reported the policy as not matching its own
# description. The screen was correct - "off" was printed directly above that
# sentence - but every description is in the present indicative, so a reader
# scanning them reads eleven statements of what the game is doing while ten
# of them are hypothetical. Verified separately that auto_open itself is not
# broken: with the policy on, auto_open_ventures does open that pawnshop.
_s_pol = sim(civ="england_1300")
_pol_out = S._agent_dispatch(_s_pol, NODES, {"cmd": "policy"})
_pol_txt = _PROTO.render_policy(_pol_out)
check("the policy screen says which automatic behaviours are running now "
      "and which are only descriptions of what would happen",
      "RUNNING NOW:" in _pol_txt and "NOT RUNNING" in _pol_txt
      and "WOULD do if you turned it on" in _pol_txt, _pol_txt[:300])
check("...with every switch still listed exactly once between the two "
      "groups, none dropped by the grouping",
      all(_k in _pol_txt for _k in (_pol_out.get("policy") or {}))
      and all(_pol_txt.count("  %-18s " % _k) == 1
              for _k in (_pol_out.get("policy") or {})),
      sorted(_pol_out.get("policy") or {}))

# AND THE THING THEY THOUGHT WAS BROKEN IS NOT BROKEN.
_s_pol2 = sim(civ="england_1300")
_s_pol2.done.add("fin_restaurant")
_s_pol2._done_changed()
check("auto_open really would open a concern that plainly pays for itself: "
      "the pawnshop's 144 to open against 250 a year clear is a payback "
      "well under a year, and auto_open_ventures takes it",
      "fin_restaurant" in _s_pol2.auto_open_ventures(),
      (NODES["fin_restaurant"]["rev"], NODES["fin_restaurant"]["up"],
       _s_pol2.venture_capex("fin_restaurant")))
check("...and it was off by default, which is the whole of why they did not "
      "see it happen",
      sim(civ="england_1300").policy.get("auto_open") is False,
      sim(civ="england_1300").policy)

# "NOTHING ELSE RESTS ON THIS" HAS TO MEAN ZERO. A naive Rome player caught
# the game contradicting itself inside a minute: `why met_ore_crushing_sorting`
# answered "HOW MUCH RESTS ON THIS: nothing else; this is worth having for
# itself", while met_jigging_gravity, visible in their own list, refused with
# "missing prerequisites: met_ore_crushing_sorting". They found the same pair
# again in in2_tape_measure_steel and in2_baseline_measurement_apparatus. The
# bottom band covered 0 through 3. Banding is the right answer to the spoiler
# problem - the exact count is a map of the tree - but a band whose words are
# false is not. Vague is allowed, wrong is not.
check("only a genuine zero is described as having nothing resting on it",
      _PROTO._rests_band(0).startswith("nothing else")
      and not any(_PROTO._rests_band(_n).startswith("nothing else")
                  for _n in (1, 2, 3, 4, 41, 301, 1201)),
      [(_n, _PROTO._rests_band(_n)) for _n in (0, 1, 2, 3, 4)])
check("...and the bands still climb, so the new rung did not break the "
      "ladder",
      len({_PROTO._rests_band(_n) for _n in (0, 1, 4, 41, 301, 1201)}) == 6,
      [_PROTO._rests_band(_n) for _n in (0, 1, 4, 41, 301, 1201)])
check("...and every band has a short form for the column that renders it",
      all(_PROTO._rests_band(_n) in _PROTO._RESTS_SHORT
          for _n in (0, 1, 4, 41, 301, 1201)),
      sorted(_PROTO._RESTS_SHORT))

# THE TWO PAIRS THEY ACTUALLY REPORTED, end to end through `why`.
_s_rb = sim()
for _a, _b in (("met_ore_crushing_sorting", "met_jigging_gravity"),
               ("in2_tape_measure_steel",
                "in2_baseline_measurement_apparatus")):
    _rb_why = S._agent_dispatch(_s_rb, NODES, {"cmd": "why", "id": _a})
    _rb_rests = _rb_why.get("how_much_rests_on_this")
    check("%s does not claim nothing rests on it, when %s names it as a "
          "missing prerequisite" % (_a, _b),
          _a in NODES[_b]["pre"]
          and not (_rb_rests or "").startswith("nothing else"),
          (_rb_rests, NODES[_b]["pre"]))

# AND THE CLASS: no node with a dependent may say nothing rests on it.
_rb_kids = collections.Counter()
for _k, _n in NODES.items():
    for _p in _n["pre"]:
        _rb_kids[_p] += 1
_rb_liars = [_k for _k in sorted(NODES)
             if _rb_kids[_k] > 0
             and _PROTO._rests_band(_rb_kids[_k]).startswith("nothing else")]
check("no node in the whole tree that something else depends on is "
      "described as having nothing resting on it",
      not _rb_liars, _rb_liars[:8])
# --- the state notices you: requisition, office, military demand, ----------
# --- confiscation as a tail risk (society.py, all five civilization files) -
# A player who had already won the game with 691 employees, 1.1 billion
# denarii, working firearms, a power grid and a railway found that the state
# had never once requisitioned output, demanded military supply, pressed an
# office, or threatened confiscation - unrealistic in a specific way, since
# state predation on large private enterprise is one of the most reliable
# facts of pre-industrial economic history. These checks are for the fix.
_ALL_CIVS = ("rome_100ad", "han_china_100ad", "england_1300", "norse_900ad",
             "mexica_1500")

for _cv in _ALL_CIVS:
    _s0 = sim(civ=_cv)
    check("%s: a fresh household is below the line - the state has not "
          "noticed it yet" % _cv,
          _s0.state_notice() < 0.02, _s0.state_notice())
    check("%s: ...and state_pressure_report() says so with nothing to show, "
          "not a sentence repeated on every dormant turn" % _cv,
          _s0.state_pressure_report() is None, _s0.state_pressure_report())
    _sp = _s0.civ.get("state_pressure") or {}
    check("%s: its civilization file carries its OWN requisition/office/"
          "military/confiscation names and notes, not a shared generic one"
          % _cv,
          all(_sp.get(k) for k in (
              "requisition_name", "requisition_note", "requisition_base_share",
              "office_name", "office_note", "office_base_share",
              "military_name", "military_note",
              "confiscation_name", "confiscation_note")),
          _sp)


def _grown(civ, employees=300.0, capital=3000000.0, eminence=20.0):
    """A household large enough to be past STATE_NOTICE_THRESHOLD on every
    civilisation whose state_capacity is not Norse's - built once here
    rather than copied into every check below.
    """
    s = sim(civ=civ, events=True)
    s.employees["artisan"] = employees
    s._resync_pools()
    s.capital = capital
    s.eminence = eminence
    s.update_protection()
    return s


_big = _grown("rome_100ad")
check("a household with 300 employees, 3,000,000 denarii and an eminence "
      "of 20 is past the general notice line for Rome (state_capacity 0.85)",
      _big.state_notice() > _big.STATE_NOTICE_THRESHOLD, _big.state_notice())
_req_share, _req_why = _big.requisition_report()
_off_share, _off_name = _big.office_report()
check("...and requisition now takes a real, nonzero share of revenue",
      _req_share > 0.0, _req_share)
check("...priced in this civilisation's own words, not a generic label",
      _off_name == _big.civ["state_pressure"]["office_name"], _off_name)
check("...and the office costs something too, alongside requisition",
      _off_share > 0.0, _off_share)

_poor_protection = _grown("rome_100ad")
_poor_protection.protection = 0.0
_rich_protection = _grown("rome_100ad")
_rich_protection.protection = 0.85
check("requisition is bargained down by protection - patronage and standing "
      "are not decorative here",
      _rich_protection.requisition_report()[0] < _poor_protection.requisition_report()[0],
      (_rich_protection.requisition_report()[0], _poor_protection.requisition_report()[0]))
check("...but the office is NOT bargained down the same way - it is the "
      "version you do not get to decline cheaply",
      abs(_rich_protection.office_report()[0] - _poor_protection.office_report()[0]) < 1e-9,
      (_rich_protection.office_report()[0], _poor_protection.office_report()[0]))

_prot_before = sim(civ="rome_100ad")
_prot_before.update_protection()
_small_protection = _prot_before.protection
_prot_after = _grown("rome_100ad")
check("being pressed into office is also a shield: crossing the notice line "
      "raises protection by itself, on top of anything built",
      _prot_after.protection > _small_protection, (_prot_after.protection, _small_protection))

_no_mil = _grown("rome_100ad")
check("no militarily significant technology done: the state has nothing to "
      "ask this household for",
      not _no_mil.military_demand_eligible(), _no_mil.military_leverage())
_mil_done = _grown("rome_100ad")
_mil_done.done.update(k for k in NODES if "military" in NODES[k].get("traits", ())
)
_mil_done._done_changed()
check("...but the FIRST working gun (one military-branch node, not a "
      "standing army) is already enough to be asked for",
      _mil_done.military_leverage() >= _mil_done.MIL_LEVERAGE_FLOOR_FOR_DEMAND
      and _mil_done.military_demand_eligible(),
      _mil_done.military_leverage())

_tiny_notice = sim(civ="rome_100ad")
_tiny_notice.employees["artisan"] = 2.0
_tiny_notice._resync_pools()
check("military demand still needs SOME visible scale - a founder who has "
      "merely studied cannon, with no household to speak of, is not yet "
      "worth a state's letter",
      not (_tiny_notice.military_leverage() >= 0.2
           and _tiny_notice.state_notice() > _tiny_notice.STATE_NOTICE_THRESHOLD_MILITARY),
      _tiny_notice.state_notice())

_huge = _grown("rome_100ad", employees=2000.0, capital=60000000.0, eminence=25.0)
check("confiscation is a TAIL risk: it stays at zero until well past the "
      "general notice line, not the moment requisition starts",
      _big.confiscation_risk()[0] == 0.0 and _big.state_notice() > _big.STATE_NOTICE_THRESHOLD,
      (_big.state_notice(), _big.confiscation_risk()[0]))
check("...and only arrives once a household is truly enormous",
      _huge.confiscation_risk()[0] > 0.0, _huge.state_notice())

_huge_bare = _grown("rome_100ad", employees=2000.0, capital=60000000.0, eminence=25.0)
_huge_shielded = _grown("rome_100ad", employees=2000.0, capital=60000000.0, eminence=25.0)
_huge_shielded.protection = 0.85
_huge_shielded.done.add("academy_network")
_huge_shielded._done_changed()
_huge_shielded.done.update(k for k in NODES if "military" in NODES[k].get("traits", ())
)
_huge_shielded._done_changed()
check("confiscation is mitigable, by exactly the things that mitigated it "
      "historically: a patron/standing, dispersed holdings, and being "
      "useful to a state that fights, ALL reduce the tail risk together",
      _huge_shielded.confiscation_risk()[0] < _huge_bare.confiscation_risk()[0],
      (_huge_shielded.confiscation_risk()[0], _huge_bare.confiscation_risk()[0]))

_norse_extreme = sim(civ="norse_900ad")
_norse_extreme.employees["artisan"] = 2000.0
_norse_extreme._resync_pools()
_norse_extreme.capital = 60000000.0
_norse_extreme.eminence = 30.0
check("Norse state_capacity (0.15) caps notice so low that even an "
      "extravagantly large household crosses no threshold here - 'the "
      "thing is an assembly, not a state' is a real mechanical floor, not "
      "only a line in the opening text",
      _norse_extreme.state_notice() < _norse_extreme.STATE_NOTICE_THRESHOLD
      and _norse_extreme.requisition_report()[0] == 0.0,
      _norse_extreme.state_notice())
_norse_built = sim(civ="norse_900ad")
_norse_built.civ["state_capacity"] = 0.9          # as if centuries of kings,
_norse_built.state_capacity = 0.9                 # bishops and taxes arrived
_norse_built.employees["artisan"] = 2000.0
_norse_built._resync_pools()
_norse_built.capital = 60000000.0
_norse_built.eminence = 30.0
check("...but a Norse state that DID build up state_capacity (the same "
      "tech-effect field every civilisation reads) is judged by the exact "
      "same rule as everyone else, not given a permanent exemption",
      _norse_built.requisition_report()[0] > 0.0, _norse_built.requisition_report())

# Fog safety (hard rule 3): nothing this mechanic prints may name a node id
# the player has not discovered. _state_pressure only ever uses this
# civilisation's own plain-language state_pressure names, never a tech id.
_fogged = _grown("rome_100ad", employees=2000.0, capital=60000000.0, eminence=25.0)
_fogged.fog = True
_fogged.year = _fogged.year
_before_log = len(_fogged.log)
_fogged._state_pressure(_fogged.year)
_new_lines = " ".join(m for _y, m in _fogged.log[_before_log:])
_leaked = [k for k in NODES if k in _new_lines]
check("the state-notices-you log lines never leak a bare node id, under fog "
      "or off it - only this civilisation's own plain historical names",
      not _leaked, _leaked[:5])

# Determinism/dice-free guarantee: the probabilistic rolls (military demand,
# confiscation) must answer to `events`, the same switch every other
# probabilistic hazard in this file already answers to - a dice-free trial
# (path_search.py's own DetRNG, events=False) must see none of them fire,
# while the deterministic tax (requisition/office) is not a "dice" and must
# apply either way.
class _AlwaysFires(random.Random):
    def random(self):
        return 0.0


_det_off = _grown("rome_100ad", employees=2000.0, capital=60000000.0, eminence=25.0)
_det_off.events = False
_det_off.rng = _AlwaysFires(1)
_cap_before_off = _det_off.capital
_det_off._state_pressure(_det_off.year)
check("with events off, the probabilistic confiscation/military rolls never "
      "actually fire even when the rng would always take them - the warning "
      "that one is APPROACHING is allowed through regardless, the same way "
      "eminence's own conspicuousness warning in core.py's step() is not "
      "gated on events either, only its dice roll is",
      not any("handed over" in m or "the state takes what it judges" in m
             for _y, m in _det_off.log[-5:]),
      [m for _y, m in _det_off.log[-5:]])
check("...but the deterministic requisition/office tax still applies - it "
      "is not a roll of the dice, and a dice-free trial must still feel it",
      _det_off.capital < _cap_before_off, (_det_off.capital, _cap_before_off))

_det_on = _grown("rome_100ad", employees=2000.0, capital=60000000.0, eminence=25.0)
_det_on.events = True
_det_on.rng = _AlwaysFires(1)
_det_on._state_pressure(_det_on.year)
check("...and with events on, the same always-fires rng DOES produce the "
      "confiscation tail event this time",
      any("the state takes what it judges" in m for _y, m in _det_on.log),
      [m for _y, m in _det_on.log[-5:]])
