"""completion_messaging: the rules behind failure severity, goal deltas and the opening shortfall are called with figures
built here; three named scenarios finish a project in a game and read the log lines' kinds and facts; the summary-first
wave is rendered from a built reply."""
import contextlib

from .harness import *  # noqa: F401,F403
from sim.engine.completion_rules import road_line, severity_of_loss, staff_shortfall
from sim.engine.projects_completion import goal_movement
from sim.refusal import cause_of
from sim.ui.proto import render_screen_step as _render_big
from sim.ui.proto.wave_summary import wave_summary

# --- Complaint 81: how loudly a failure speaks follows the loss against the player's means and the goal's road.
MINOR_SHARE, ROAD_WEIGHT, MEANS = 0.05, 2.0, 1000.0
small_loss = MINOR_SHARE * MEANS * 0.75
check("a loss under the minor share of means reads minor off the goal road",
      severity_of_loss(small_loss, MEANS, False, MINOR_SHARE, ROAD_WEIGHT) == "minor")
check("...and major when the failed project is on the goal road, which weights the loss up",
      severity_of_loss(small_loss, MEANS, True, MINOR_SHARE, ROAD_WEIGHT) == "major")
check("a loss exactly at the minor share is major, not minor",
      severity_of_loss(MINOR_SHARE * MEANS, MEANS, False, MINOR_SHARE, ROAD_WEIGHT) == "major")
check("means under one are read as one, so a vanishing purse does not make every loss major at zero",
      severity_of_loss(0.0, 0.0, False, MINOR_SHARE, ROAD_WEIGHT) == "minor"
      and severity_of_loss(1.0, 0.0, False, MINOR_SHARE, ROAD_WEIGHT) == "major")

# --- Complaint 127 (completion half): the shortfall is reported when today's free staff could not supervise it.
check("a concern needing more scholars than are free is a shortfall carrying all four figures",
      staff_shortfall(5.0, 5.0, 0.0, 9.0) == (5.0, 5.0, 0.0, 9.0))
check("...and so is one needing more craftsmen than are free",
      staff_shortfall(1.0, 6.0, 4.0, 5.0) == (1.0, 6.0, 4.0, 5.0))
check("...and there is none when the free staff cover the need", staff_shortfall(5.0, 5.0, 50.0, 50.0) is None)
check("...a need within the rounding tolerance of the free staff is covered",
      staff_shortfall(5.005, 5.0, 5.0, 5.0) is None)

# --- Complaint 83: goal deltas, shown before and after, on a completion that moves the goal metric.
before_snapshot = {"measures": {"literacy general": (0.10, True), "ceiling": (0.35, True)}, "road_done": 3}
after_snapshot = {"measures": {"literacy general": (0.15, True), "ceiling": (0.35, True)}, "road_done": 4}
moved, gained = goal_movement(before_snapshot, after_snapshot)
check("a measure that moved is reported as before and after, as percentages, and one that did not is left out",
      moved == [("literacy general", "10.0%", "15.0%")] and gained == 1, (moved, gained))
check("nothing moved, nothing reported", goal_movement(before_snapshot, before_snapshot) == ([], 0))
check("no goal, no movement", goal_movement(None, after_snapshot) == ([], 0))
check("a completion on the road to the goal says how far along it is", "3 of 9 steps" in road_line(False, 3, 9),
      road_line(False, 3, 9))
check("under fog the road line never reveals the total", " of " not in road_line(True, 3, 9), road_line(True, 3, 9))


# --- SCENARIOS: a project finished in a game, the lines it logs read by kind and facts (a finished node cannot be
# finished again, so each game finishes a node once, and what a scenario swaps in is put back after it).
def _finish(test_sim, node_id, failing=False):
    """Run one attempt at `node_id` to its end and return the log lines it added."""
    test_sim.effective_risk = lambda _node_id: 1.0 if failing else 0.0
    test_sim.state.projects.active.pop(node_id, None)   # a failed attempt leaves its project active
    test_sim.initialize_project(node_id, ph_left=0.0)
    before = len(test_sim.log)
    test_sim._complete(node_id)
    return [message for _year, message in test_sim.log[before:]]


@contextlib.contextmanager
def _swapped(game, **replacements):
    """Replace attributes on one game for the length of a block."""
    held = {name: game.__dict__.get(name, _ABSENT) for name in replacements}
    for name, value in replacements.items():
        setattr(game, name, value)
    try:
        yield
    finally:
        for name, value in held.items():
            if value is _ABSENT:
                game.__dict__.pop(name, None)
            else:
                setattr(game, name, value)


_ABSENT = object()

game_one, game_two = sim(), sim()

with _swapped(game_one, funding_capacity=lambda: 1e12):
    minor_lines = _finish(game_one, "school_founded", failing=True)
with _swapped(game_one, funding_capacity=lambda: 1.0):
    major_lines = _finish(game_one, "school_founded", failing=True)
check("scenario: a failing attempt logs one project_failed line, minor when small against the means",
      [cause_of(line) for line in minor_lines] == ["project_failed"] and minor_lines[0].facts["severity"] == "minor",
      minor_lines)
check("scenario: ...and major when large against the means",
      [cause_of(line) for line in major_lines] == ["project_failed"] and major_lines[0].facts["severity"] == "major",
      major_lines)

with _swapped(game_two, venture_staff_free=lambda: (0.0, 0.0), venture_hands=lambda node_id: (5.0, 5.0)):
    short_lines = _finish(game_two, "school_founded")
check("scenario: a finished concern is logged as completed, and as a shortfall when the free staff cannot open it",
      [cause_of(line) for line in short_lines if cause_of(line) in ("project_completed", "opening_shortfall")]
      == ["project_completed", "opening_shortfall"], short_lines)
# presentation: the completion line's closed-status wording and what it says switches on at opening (Complaint 84)
check("scenario: a finished concern says it is closed, how to open it and what switches on when it opens",
      any("STATUS: CLOSED" in line and "open school_founded" in line and "Scholar and artisan training" in line
          for line in map(str, short_lines)), short_lines)
held_goal = game_two.goal
game_two.goal = "goal_literacy_common"
game_two.set_literacy("literacy_general", 0.10)
with _swapped(game_two, apply_tech_effects=lambda node_id: game_two.set_literacy("literacy_general", 0.15)):
    goal_lines = _finish(game_two, "ag2_balanced_ration")
game_two.goal = held_goal
check("scenario: a completion that moves the goal metric logs a goal_effect line",
      "goal_effect" in [cause_of(line) for line in goal_lines]
      and "opening_shortfall" not in [cause_of(line) for line in goal_lines], goal_lines)
# presentation: a piece of knowledge is not announced as a closed concern
check("scenario: a piece of knowledge does not claim to be closed",
      not any("STATUS: CLOSED" in str(line) for line in goal_lines))

# --- Complaint 80: summary first.
wave = [{"id": "a%d" % index, "name": "Thing %d" % index, "year": 200,
         "granted": False, "kind": "technology"} for index in range(12)]
wave.append({"id": "c1", "name": "Shop", "year": 200, "granted": False, "kind": "concern"})
# reply events carry the log line's kind and facts (Complaint 521); the summary reads those, not the wording
events = [{"year": 200, "message": "FAILED at X (minor): lost 3.", "event_kind": "project_failed",
           "facts": {"severity": "minor"}},
          {"year": 200, "message": "FAILED at Y: it did not work.", "event_kind": "project_failed",
           "facts": {"severity": "major"}}]
summary = wave_summary(wave, events, goal_before=None, goal_after=None)
check("summary counts completions by kind and failures by severity",
      summary["completed"] == 13 and summary["by_kind"] == {"technology": 12, "concern": 1}
      and summary["failed"] == 2 and summary["minor_failures"] == 1, summary)
check("no summary for a quiet step", wave_summary([], [], None, None) is None)

# presentation: the layout of a step reply, the summary line printed before the detail
rendered = _render_big.render_step(dict(ok=True, completed=wave, events=events,
                                        lost=[], summary=summary, year=200))
lines = rendered.splitlines()
summary_at = next(i for i, line in enumerate(lines) if "13 completed" in line)
detail_at = next(i for i, line in enumerate(lines) if "Thing 0" in line)
check("a large wave prints its one-line summary before the detail",
      summary_at < detail_at and "2 failed" in lines[summary_at], lines[:4])
small = dict(ok=True, completed=wave[:2], events=[], lost=[],
             summary=wave_summary(wave[:2], [], None, None), year=200)
check("a small wave stays a plain list with no summary line",
      "completed (" not in _render_big.render_step(small))
