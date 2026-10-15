"""completion_messaging: failure severity, goal deltas, built-not-open status and summary-first waves."""
import contextlib

from .harness import *  # noqa: F401,F403
from sim.ui.proto import render_screen_step as _render_big
from sim.ui.proto.wave_summary import wave_summary


def _finish(test_sim, node_id, failing=False):
    """Run one attempt at `node_id` to its end and return the log lines it added."""
    test_sim.effective_risk = lambda _node_id: 1.0 if failing else 0.0
    test_sim.state.projects.active.pop(node_id, None)   # a failed attempt leaves its project active
    test_sim.initialize_project(node_id, ph_left=0.0)
    before = len(test_sim.log)
    test_sim._complete(node_id)
    return [message for _year, message in test_sim.log[before:]]


# Three games carry every check; a finished node cannot be finished again, so
# each game finishes a node once, and what a check swaps in is put back after it.
game_one, game_two, game_three = sim(), sim(), sim()


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

# --- Complaint 81: failure narrative scales with consequence.
with _swapped(game_one, funding_capacity=lambda: 1e12):
    minor_lines = _finish(game_one, "school_founded", failing=True)
with _swapped(game_one, funding_capacity=lambda: 1.0):
    major_lines = _finish(game_one, "school_founded", failing=True)
check("a failure that is small next to your means is one compact line",
      len(minor_lines) == 1 and minor_lines[0].startswith("FAILED at")
      and "minor" in minor_lines[0] and len(minor_lines[0]) < 160, minor_lines)
check("a failure that is large next to your means keeps the full consequences",
      len(major_lines) == 1 and "minor" not in major_lines[0]
      and "hours are to do again" in major_lines[0], major_lines)

means = 1000.0
small_loss = game_one.MINOR_FAILURE_SHARE * means * 0.75
off_path = next(node_id for node_id in NODES if node_id not in game_one.goal_closure_ids())
on_path = next(node_id for node_id in game_one.goal_closure_ids())
check("the same loss reads minor off the goal path",
      game_one.failure_severity(off_path, small_loss, means) == "minor")
check("...and major when the failed project is on the goal path",
      game_one.failure_severity(on_path, small_loss, means) == "major")

# --- Complaint 84: built is not open.
closed_lines = _finish(game_one, "school_founded")
check("a finished concern says it is closed and how to open it",
      any("STATUS: CLOSED" in line and "open school_founded" in line
          for line in closed_lines), closed_lines)
check("...and names what switches on when it opens",
      any("Scholar and artisan training" in line for line in closed_lines), closed_lines)
check("a piece of knowledge does not claim to be closed",
      not any("STATUS: CLOSED" in line
              for line in _finish(game_one, "ag2_balanced_ration")))

# --- Complaint 127 (completion half): say when today's staff could not open it.
with _swapped(game_two, venture_staff_free=lambda: (0.0, 0.0),
              venture_hands=lambda node_id: (5.0, 5.0)):
    short_lines = _finish(game_two, "school_founded")
check("a finished concern you lack the staff to open says so",
      any("could not open it" in line for line in short_lines), short_lines)
with _swapped(game_three, venture_staff_free=lambda: (50.0, 50.0)):
    staffed_lines = _finish(game_three, "school_founded")
check("...and stays quiet when the staff are free",
      not any("could not open it" in line for line in staffed_lines))

# --- Complaint 83: goal deltas on completion.
held_goal, held_literacy = game_two.goal, game_two.civ.get("literacy_general")
game_two.goal = "goal_literacy_common"
game_two.civ["literacy_general"] = 0.10
with _swapped(game_two, apply_tech_effects=lambda node_id: game_two.civ.__setitem__("literacy_general", 0.15)):
    goal_lines = _finish(game_two, "ag2_balanced_ration")
game_two.goal = held_goal
game_two.civ["literacy_general"] = held_literacy
check("a completion that moves the goal metric shows before and after",
      any("goal effect" in line and "10.0%" in line and "15.0%" in line
          for line in goal_lines), goal_lines)
held_goal = game_three.goal
game_three.goal = "goal_literacy_common"
with _swapped(game_three, goal_closure_ids=lambda: set(), apply_tech_effects=lambda node_id: None,
              literacy_ceiling_general=lambda: 0.35):
    unmoved_lines = _finish(game_three, "ag2_balanced_ration")
game_three.goal = held_goal
check("a completion that moves nothing on the goal adds no goal line",
      not any("goal effect" in line for line in unmoved_lines))

path_node = sorted(game_one.goal_closure_ids())[0]
path_lines = _finish(game_one, path_node)
check("a completion on the road to the goal says so",
      any("goal effect" in line and "road" in line for line in path_lines), path_lines)
held_fog = game_two.fog
game_two.fog = True
fog_lines = _finish(game_two, sorted(game_two.goal_closure_ids())[0])
game_two.fog = held_fog
check("under fog the road line never reveals the total",
      any("goal effect" in line for line in fog_lines)
      and not any(" of " in line for line in fog_lines if "goal effect" in line), fog_lines)

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
