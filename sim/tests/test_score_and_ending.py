"""The score and the ending: the weights, the goal gate, fog, the achievements and the points scale, each called on a
stand-in game with the values the test sets (`score_game.ScoreGame`, no game is run). The institutions component, whose sum must not
depend on set order, is test_score_institutions."""
from .harness import check, NODES, GOAL, S

from sim.refusal import cause_of
from sim.tests.score_game import ScoreGame
from sim.ui.protocol import score_report as _score, render_score as _render_score, SCORE_WEIGHTS, \
    final_report as _final_report

QUICK_TOPIC = True


def _game(**fields):
    game = ScoreGame(NODES, goal=GOAL)
    for name, value in fields.items():
        setattr(game, name, value)
    return game


def _horizon_year(game):
    return game.cfg["start_year"] + game.cfg["horizon_years"]


check("score is advertised in KNOWN_COMMANDS", "score" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)
check("the seven weights sum to exactly 1.0, so the total is a real percentage",
      len(SCORE_WEIGHTS) == 7 and abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9, SCORE_WEIGHTS)

# --- the gate: no goal, no flagged-reached total, but a total all the same
game = _game()
game.year = _horizon_year(game)
report_nogoal = _score(game, NODES)
check("a run that ends without the goal still gets its total, flagged goal not reached",
      report_nogoal["total"] is not None and report_nogoal["points"] is not None
      and bool(report_nogoal.get("goal_not_reached")) and not report_nogoal["goal_reached"],
      report_nogoal["total"])
check("...and the rendered ending screen shows the total with the flag",
      "TOTAL: " in _render_score(report_nogoal) and "goal not reached" in _render_score(report_nogoal)
      and "TOTAL: --" not in _render_score(report_nogoal))

report_mid = _score(_game(), NODES)
check("mid-run, before the goal and the horizon, every component is shown with its raw figure",
      report_mid["total"] is not None and not report_mid["goal_reached"]
      and all(component.get("raw") is not None for component in report_mid["components"].values())
      and set(report_mid["components"]) == set(SCORE_WEIGHTS), list(report_mid["components"]))
check("each weighted figure is the normalized one times its weight",
      all(abs(component["weighted"] - round(component["normalized"] * SCORE_WEIGHTS[name], 4)) < 1e-9
          for name, component in report_mid["components"].items()))

# --- fog: the tree's total size stays hidden until the run ends
game = _game(fog=True, done={"a", "b", "c"})
coverage_mid = _score(game, NODES)["components"]["technology_coverage"]
check("under fog, mid-run, coverage withholds the tree's total and its normalized value but keeps the raw count",
      coverage_mid["normalized"] is None and coverage_mid["of_total"] is None and coverage_mid["raw"] == 3,
      coverage_mid)
check("...and the rendered screen never prints the tree's total node count while withheld",
      str(len(NODES)) not in _render_score(_score(game, NODES)))
check("...so the total is not computable and the screen says so",
      _score(game, NODES)["total"] is None and "TOTAL: --" in _render_score(_score(game, NODES)))
game.year = _horizon_year(game)
coverage_end = _score(game, NODES)["components"]["technology_coverage"]
check("once the run ends, fog lifts exactly this one number",
      coverage_end["normalized"] == 3 / len(NODES) and coverage_end["of_total"] == len(NODES), coverage_end)
check("off fog, coverage is visible at once, mid-run",
      _score(_game(done={"a"}), NODES)["components"]["technology_coverage"]["normalized"] is not None)

# --- the end reason under fog
game = _game(fog=True)
game.year = _horizon_year(game)
game.goal_year = game.cfg["start_year"] + 5
import sim.ui.proto.state_waiting as _waiting
check("under fog, a player who reached the goal and kept building to the horizon is told they reached it",
      cause_of(_waiting._agent_end_reason(game)) == "horizon_goal_reached")
game.goal_year = None
check("...while one who never reached it under fog is told so",
      cause_of(_waiting._agent_end_reason(game)) == "horizon_goal_missed")

# --- achievements: each flips on its own field, and none fire before the goal
def _achievements(**fields):
    game = _game(**fields)
    game.goal_year = game.year + 1 if "goal_year" not in fields else fields["goal_year"]
    return _score(game, NODES)["achievements"]


clean = _achievements()
check("a clean won run earns every achievement but the pace one, which has its own checks",
      all(entry["won"] for name, entry in clean.items() if name != "outpaced_the_fastest_plan"), clean)
check("a run that never reached the goal earns no achievement at all", _score(_game(), NODES)["achievements"] == {})
sacked = _achievements(forgotten={"corpus_written": 300})
check("a sacking that forgot one technology costs only the corpus achievement",
      not sacked["corpus_intact"]["won"] and sacked["never_understaffed"]["won"]
      and sacked["free_hands_only"]["won"] and sacked["clean_ledger"]["won"], sacked)
game = _game()
game.ever_closed_for_staff.add("workshop_first")
game.goal_year = game.year + 1
understaffed = _score(game, NODES)["achievements"]
check("a concern once closed for want of staff costs only that achievement",
      not understaffed["never_understaffed"]["won"] and understaffed["corpus_intact"]["won"], understaffed)
check("a concern shut for staff now costs it too",
      not _achievements(shut_for_staff={"workshop_first": 150})["never_understaffed"]["won"])
insolvent = _achievements(insolvent_years=1)
check("one insolvent year costs the clean-ledger achievement only",
      not insolvent["clean_ledger"]["won"] and insolvent["corpus_intact"]["won"], insolvent)
check("a single coin of interest paid costs it on its own",
      not _achievements(interest_paid=0.01)["clean_ledger"]["won"])
slaveholder = _achievements(slaves=1)
check("owning one slave costs only the free-hands achievement",
      not slaveholder["free_hands_only"]["won"] and slaveholder["clean_ledger"]["won"], slaveholder)
check("having freed a slave counts against it as well",
      not _achievements(manumitted_total=1)["free_hands_only"]["won"])
# the goal's own fastest timeline is the floor; twice it is the bar
check("reaching the goal within twice the critical-path floor outpaces the fastest plan",
      _achievements(goal_year=100 + 40)["outpaced_the_fastest_plan"]["won"])
check("...and one year over twice the floor does not",
      not _achievements(goal_year=100 + 41)["outpaced_the_fastest_plan"]["won"])

# --- the ending screen and the points scale
game = _game(done={sorted(NODES)[0]})
game.goal_year = game.year + 1
game.year = _horizon_year(game)
final = _final_report(game, NODES)
check("the ending screen's final_report carries the score",
      final.get("score", {}).get("total") is not None, final.get("score"))
check("points are an exact rescaling of the same capped total, 1000 for a perfect run",
      final["score"]["points"] == round(final["score"]["total"] * 1000), final["score"])
check("a run that missed the goal has a points figure too",
      report_nogoal["points"] == round(report_nogoal["total"] * 1000))

perfect = _game(reputation=1e9, scandal=-1e9, capital=1e30, headcount=1e9, done=set(NODES),
                literacy_values={"literacy_general": 1e9, "literacy_elite": 1e9},
                units={"workshop_first": 1e9, "school_founded": 1e9},
                operating={"workshop_first", "school_founded", "identity_cover"})
perfect.goal_year = perfect.year + 1
report_perfect = _score(perfect, NODES)
check("a household built to overdrive every component cannot pass 100% or 1000 points",
      report_perfect["total"] <= 1.0 + 1e-9 and report_perfect["points"] <= 1000,
      (report_perfect["total"], report_perfect["points"]))
check("...and every component is clamped to one on its own",
      all(component["normalized"] <= 1.0 + 1e-9 for component in report_perfect["components"].values()),
      {name: component["normalized"] for name, component in report_perfect["components"].items()})

# --- literacy is printed as a percentage against its ceiling
literate = _game(literacy_values={"literacy_general": 0.0749, "literacy_elite": 0.9})
literate_reply = _score(literate, NODES)
literacy_line = next(line for line in _render_score(literate_reply).splitlines() if line.strip().startswith("literacy"))
literacy_detail = literate_reply["components"]["literacy"]["raw_detail"]
# presentation: the score prints literacy as a percentage, not a raw fraction
check("score prints general literacy as a percentage, not a raw fraction", "7.49%" in literacy_line, literacy_line)
# presentation: the figure is printed against its ceiling
check("score prints the literacy figure against its ceiling",
      "%.2f%%" % (literacy_detail["general_ceiling"] * 100) in literacy_line, (literacy_line, literacy_detail))
check("the literacy share is half the general and half the elite share of each ceiling",
      abs(literate_reply["components"]["literacy"]["normalized"]
          - (0.5 * min(1.0, 0.0749 / 0.2) + 0.5 * min(1.0, 0.9 / 0.8))) < 1e-9)
