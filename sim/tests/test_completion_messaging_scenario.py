"""SCENARIO (Complaint 640): a project finished in a game, the log lines it adds read by kind and facts. The severity, goal
movement and shortfall rules are called on built figures in test_completion_messaging."""
import contextlib

from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of

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
