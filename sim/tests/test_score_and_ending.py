"""score_and_ending: regression checks, run individually with `--only score_and_ending`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

# =============================================================================
# THE SCORE AND THE ENDING. A player who had just won asked for a score,
# weighted across seven things, goal-gated ("no score: the goal was not
# reached"), inspectable mid-run, and respectful of fog - plus a short
# achievements list. See engine/protocol.py's own block comment above
# SCORE_WEIGHTS for which field feeds each component and why.
# =============================================================================
from sim.ui.protocol import (score_report as _SCORE, render_score as _RSCORE,
                             SCORE_WEIGHTS as _SW)

check("score is advertised in KNOWN_COMMANDS, the same way capacity/economy/"
      "changes were",
      "score" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)
check("the seven weights sum to exactly 1.0, so the total is a real "
      "percentage, not one that quietly falls short of or past 100%",
      abs(sum(_SW.values()) - 1.0) < 1e-9, _SW)

_score_game = sim(capital=5_000_000.0)   # one game; each check below sets the year, fog and goal it needs
_score_start_year = _score_game.year
_score_horizon_year = _score_game.cfg["start_year"] + _score_game.cfg["horizon_years"]
_score_goal_year = _score_game.goal_year
_sc_win = S._agent_dispatch(_score_game, NODES, {"cmd": "score"})
check("`score` answers through the command dispatcher with its components",
      _sc_win.get("ok") and "components" in _sc_win, _sc_win)

# --- THE GATE: no goal, no score, not a number. ---
_score_game.year = _score_horizon_year
_rep_nogoal = _SCORE(_score_game, NODES)
check("a run that ends without the goal still gets its total, flagged "
      "goal not reached",
      _rep_nogoal["total"] is not None and _rep_nogoal["points"] is not None
      and _rep_nogoal["goal_not_reached"] == "goal not reached",
      _rep_nogoal["total"])
check("...and the rendered ending screen shows the total with the flag",
      "TOTAL: " in _RSCORE(_rep_nogoal) and "goal not reached" in _RSCORE(_rep_nogoal)
      and "TOTAL: --" not in _RSCORE(_rep_nogoal),
      _RSCORE(_rep_nogoal))

# --- MID-RUN: inspectable before the goal is reached.
_score_game.year = _score_start_year
_rep_mid = _SCORE(_score_game, NODES)
check("mid-run, before the goal and before the horizon, `score` still "
      "shows every component - what you are optimising, not only what you "
      "already won",
      _rep_mid["total"] is not None and not _rep_mid["goal_reached"]
      and all(component.get("raw") is not None for component in _rep_mid["components"].values()),
      _rep_mid["components"].keys())

# --- FOG: the tree's TOTAL size is not visible under fog, so technology_coverage
# withholds its normalized value and denominator until the run ends.
_score_game.fog = True
_rep_fogmid = _SCORE(_score_game, NODES)
_tc_fogmid = _rep_fogmid["components"]["technology_coverage"]
check("under fog, mid-run, technology coverage withholds the tree's total "
      "and its own normalized value but keeps the raw done-count",
      _tc_fogmid["normalized"] is None and _tc_fogmid["of_total"] is None
      and _tc_fogmid["raw"] == len(_score_game.done),
      _tc_fogmid)
check("...and the rendered screen never prints the tree's total node count "
      "while withheld",
      str(len(NODES)) not in _RSCORE(_rep_fogmid), _RSCORE(_rep_fogmid))
_score_game.year = _score_horizon_year
_tc_fogend = _SCORE(_score_game, NODES)["components"]["technology_coverage"]
check("once the run ends, fog lifts exactly this one number",
      _tc_fogend["normalized"] is not None
      and _tc_fogend["of_total"] == len(NODES), _tc_fogend)

# --- _agent_end_reason's fog branch never checked goal_year, so a player who
# won under fog and kept building was told at the horizon they did not reach it.
_score_game.goal_year = _score_start_year + 5
_end_wonfog = S._agent_end_reason(_score_game)
check("BREAK: under fog, a player who reached the goal and kept building "
      "to the horizon is told they reached it, not that they did not",
      "did not reach" not in _end_wonfog and "reached" in _end_wonfog,
      _end_wonfog)
_score_game.goal_year = _score_goal_year
check("...while a player who never reached it under fog still reads the "
      "honest 'did not reach' message, unchanged",
      "did not reach" in S._agent_end_reason(_score_game), None)
_score_game.fog = False
_score_game.year = _score_start_year
check("off fog, technology coverage is visible immediately, mid-run - fog "
      "is the only thing that ever withholds it",
      _SCORE(_score_game, NODES)["components"]["technology_coverage"]["normalized"]
      is not None, None)


# --- ACHIEVEMENTS: each one flips on its own tracked field, in isolation,
# and none of them fire before the goal is reached at all.
def _achievements(**extra):
    """Achievements for the shared game with a goal reached next year and the given fields overridden."""
    saved = {name: getattr(_score_game, name, None) for name in extra}   # an unset field reads as missing
    saved_goal_year = _score_game.goal_year
    _score_game.goal_year = _score_game.year + 1
    for name, value in extra.items():
        setattr(_score_game, name, value)
    try:
        return _SCORE(_score_game, NODES)["achievements"]
    finally:
        for name, value in saved.items():
            setattr(_score_game, name, value)
        _score_game.goal_year = saved_goal_year


_ach_clean = _achievements()
check("a clean won run earns every achievement this suite can isolate",
      all(achievement["won"] for name, achievement in _ach_clean.items()
          if name != "outpaced_the_fastest_plan"),
      _ach_clean)
check("...and a run that never reached the goal earns none at all - no "
      "achievement fires on an unfinished run",
      _SCORE(_score_game, NODES)["achievements"] == {},
      _SCORE(_score_game, NODES)["achievements"])

_ach_sack = _achievements(forgotten={"corpus_written": 300})
check("BREAK-style isolation: a sacking that forgot even one technology "
      "costs only the corpus achievement, not the others",
      not _ach_sack["corpus_intact"]["won"]
      and _ach_sack["never_understaffed"]["won"]
      and _ach_sack["free_hands_only"]["won"], _ach_sack)

_score_game.state.projects.closures["workshop_first"] = {"reason": "staff", "year": 150}
_ach_staff = _achievements()
_score_game.state.projects.closures.pop("workshop_first")
check("...a concern once closed for want of staff costs only that "
      "achievement",
      not _ach_staff["never_understaffed"]["won"]
      and _ach_staff["corpus_intact"]["won"], _ach_staff)

_ach_debt = _achievements(insolvent_years=1)
check("...one insolvent year costs the clean-ledger achievement",
      not _ach_debt["clean_ledger"]["won"]
      and _ach_debt["corpus_intact"]["won"], _ach_debt)
_ach_interest = _achievements(interest_paid=0.01)
check("...and so does a single denarius of interest paid, on its own",
      not _ach_interest["clean_ledger"]["won"], _ach_interest)

_ach_slave = _achievements(slaves=1)
check("...owning even one slave costs only the free-hands achievement",
      not _ach_slave["free_hands_only"]["won"]
      and _ach_slave["clean_ledger"]["won"], _ach_slave)

_ach_fast = _achievements(goal_year=_score_game.cfg["start_year"] + 1)
check("reaching the goal almost immediately outpaces twice its own "
      "critical-path floor",
      _ach_fast["outpaced_the_fastest_plan"]["won"], _ach_fast)
_ach_slow = _achievements(goal_year=_score_game.cfg["start_year"] + 5000)
check("...while dawdling to five thousand years after the start does not",
      not _ach_slow["outpaced_the_fastest_plan"]["won"], _ach_slow)

# --- DETERMINISM: institutions sums floats over CAPABILITY_INSTITUTIONS, a
# frozenset, so this has to be proven under a different PYTHONHASHSEED.
def _score_snapshot(seed_env):
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; import random; from sim import simulator as S; "
         "from sim.ui.protocol import score_report as SC; "
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
        capture_output=True, text=True, timeout=60, cwd=ROOT,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return proc.stdout.strip()
_score_seed_a, _score_seed_b = _par_map(_score_snapshot, ("0", "98765"))
check("the institutions component, and the total it feeds, are identical "
      "under a different PYTHONHASHSEED",
      _score_seed_a == _score_seed_b and _score_seed_a,
      (_score_seed_a, _score_seed_b))

# --- THE ENDING SCREEN carries the score.
_score_game.goal_year = _score_game.year + 1
_score_game.year = _score_horizon_year
_final_sc = _FRPT(_score_game, NODES)
check("the ending screen's final_report carries the score, not just the "
      "road-to-the-goal tally it already had",
      _final_sc.get("score", {}).get("total") is not None, _final_sc.get("score"))
check("points is a lossless, exact rescaling of the SAME capped total - "
      "1000 for a perfect run - never a second figure computed some other "
      "way that could disagree with the percentage",
      _final_sc["score"]["points"] == round(_final_sc["score"]["total"] * 1000),
      (_final_sc["score"]["points"], _final_sc["score"]["total"]))
check("a run that missed the goal has a points figure too, the same "
      "rescaled total",
      _rep_nogoal.get("points") == round(_rep_nogoal["total"] * 1000),
      _rep_nogoal.get("points"))
# PERFECT SCORE NEVER EXCEEDS 1000, confirmed against a household built to
# max out every component at once.
_s_perfect = sim(capital=5_000_000.0)
_s_perfect.goal_year = _s_perfect.year + 1
_s_perfect.reputation = 1e9
_s_perfect.scandal = -1e9
_s_perfect.done = set(NODES)
_s_perfect._done_changed()
_s_perfect.inst_units = {institution: 1e9 for institution in _s_perfect.SCALABLE_INSTITUTIONS}
for _cik in _s_perfect.CAPABILITY_INSTITUTIONS:
    _s_perfect.operating.add(_cik)
_rep_perfect = _SCORE(_s_perfect, NODES)
check("even a household built to overdrive every single component at "
      "once cannot push the percentage past 100% or the points past 1000",
      _rep_perfect["total"] <= 1.0 + 1e-9
      and _rep_perfect["points"] <= 1000,
      (_rep_perfect["total"], _rep_perfect["points"]))
