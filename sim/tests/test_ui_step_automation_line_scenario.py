"""Scenarios (Complaints 91, 74 and 640): the step reply of a played game carries the automation rows of the year just
played and not an older year's, and its text carries the short state and one pointer to the full one. The rules are in
test_ui_step_automation_line."""
from sim.ui.proto.render_screen_step import render_step
from sim.ui.protocol import _agent_dispatch

from .harness import NODES, check, unopened_sim

def _game():
    """A game whose year skips the market clearing (most of a step's cost): these checks read the step reply, not prices."""
    test_sim = unopened_sim(surveyed=())
    test_sim._step_market = lambda: None
    return test_sim


game = _game()
game.end_year = game.cfg["start_year"] + 50
game.state.household.automation_audit.append(
    {"year": game.year, "policy": "auto_hire", "action": "hire", "what": "probe", "reason": "probe", "cost": 0})
reply = _agent_dispatch(game, NODES, {"cmd": "step"})
check("a row from the year just played reaches the step reply",
      any(row.get("what") == "probe" for row in reply.get("automation") or []), sorted(reply)[:40])
reply = _agent_dispatch(game, NODES, {"cmd": "step"})
check("an older year's row is not repeated in the next step",
      not any(row.get("what") == "probe" for row in reply.get("automation") or []))

# The step reply shows the short state and one closing pointer to the full one.
from sim.ui.proto.render_screen_state_views import render_view
from sim.ui.proto.render_screen_step import FULL_STATE_POINTER

step_game = _game()
step_game.end_year = step_game.cfg["start_year"] + 50
step_reply = _agent_dispatch(step_game, NODES, {"cmd": "step", "years": 2})
step_text = render_step(step_reply)
short_lines = {line for line in render_view(step_reply, "short") if line.strip()}
full_only_lines = {line for line in render_view(step_reply, "full") if line.strip()} - short_lines
# presentation: the step text is compared line by line with the short and full state renderings
check("the step reply text carries the short state's sections",
      any("state full" in line for line in short_lines) and all(line in step_text for line in short_lines if "more:" in line),
      step_text[-300:])
# presentation: as above
check("the step reply text leaves out the sections only the full state prints",
      full_only_lines and not any(line in step_text.splitlines() for line in full_only_lines), sorted(full_only_lines)[:3])
# presentation: the pointer line
check("the pointer to the full state appears exactly once, as the last line",
      step_text.count(FULL_STATE_POINTER) == 1 and step_text.splitlines()[-1] == FULL_STATE_POINTER, step_text[-200:])
