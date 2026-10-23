"""completion_messaging: the rules behind failure severity, goal deltas and the opening shortfall are called with figures
built here; the summary-first wave is rendered from a built reply. The three scenarios that finish a project in a game
and read the log lines' kinds and facts are test_completion_messaging_scenario."""
QUICK_TOPIC = True

from .harness import check
from sim.engine.completion_rules import road_line, severity_of_loss, staff_shortfall
from sim.engine.projects_completion import goal_movement
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
