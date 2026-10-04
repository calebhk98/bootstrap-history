"""The step reply and screen say what automation and the standing programme did (Complaints 91, 74)."""
from sim.ui.proto.render_screen_step import render_step
from sim.ui.proto.step_automation import automation_lines
from sim.ui.protocol import _agent_dispatch

from .harness import NODES, check, sim

rows = [{"year": 101, "policy": "auto_hire", "action": "hire", "what": "2 smiths", "reason": "short", "cost": 120},
        {"year": 101, "policy": "auto_hire", "action": "hire", "what": "1 scribe", "reason": "short", "cost": 80},
        {"year": 101, "policy": "auto_open", "action": "reopen", "what": "a mill", "reason": "staffed", "cost": 0}]
line = automation_lines(rows)
check("automation is one line counting each policy's actions with their capital",
      len(line) == 1 and "auto_hire hire x2, 200" in line[0] and "auto_open reopen x1" in line[0], line)
check("no automation rows means no line", automation_lines([]) == [])

screen = render_step({"ok": True, "completed": [], "events": [], "automation": rows,
                      "programme": [{"year": 101, "what": "goal route", "started": [], "skipped": [],
                                     "spent": 0.0, "did_nothing_because": "paused"}]})
check("the step screen shows the automation line and the programme block",
      "AUTOMATION:" in screen and "PROGRAMME:" in screen and "paused" in screen, screen[-400:])

game = sim()
game.end_year = game.cfg["start_year"] + 50
game.state.household.automation_audit.append(
    {"year": game.year, "policy": "auto_hire", "action": "hire", "what": "probe", "reason": "probe", "cost": 0})
reply = _agent_dispatch(game, NODES, {"cmd": "step"})
check("a row from the year just played reaches the step reply",
      any(row.get("what") == "probe" for row in reply.get("automation") or []), sorted(reply)[:40])
reply = _agent_dispatch(game, NODES, {"cmd": "step"})
check("an older year's row is not repeated in the next step",
      not any(row.get("what") == "probe" for row in reply.get("automation") or []))
