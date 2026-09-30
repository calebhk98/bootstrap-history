"""Complaints 149 and 158: `why` names the specialist foreman `open` will
demand, and its serial floor counts only what is still unbuilt."""
from .harness import *
from sim.engine.proto.render import render_pretty
from sim.engine.critical_path_remaining import remaining_critical_path_years
from sim.engine.data import closure, critical_path

game = sim()
foreman_node = "tex_horizontal_loom"
trade, share = game.venture_foreman(foreman_node)
why_out = S._agent_dispatch(game, NODES, {"cmd": "why", "id": foreman_node})
text = render_pretty("why", why_out)
check("why shows the specialist foreman trade and share open enforces",
      trade is not None and ("%s FTE" % trade) in text and ("%.2f" % share) in text,
      text)

goal = "point_contact_transistor"
whole = critical_path(NODES, goal)[0]
check("with nothing built the remaining floor equals the from-scratch floor",
      abs(remaining_critical_path_years(NODES, goal, set()) - whole) < 1e-9)
done_all = set(NODES) - {goal}
own = remaining_critical_path_years(NODES, goal, done_all)
check("with every prerequisite built only the goal's own time remains",
      0 < own < whole, (own, whole))
check("a finished goal has no floor left",
      remaining_critical_path_years(NODES, goal, set(NODES)) == 0.0)
check("an active node counts its remaining time, not its floor",
      remaining_critical_path_years(NODES, goal, done_all, {goal: 0.25}) == 0.25)

fresh = S._agent_dispatch(sim(), NODES, {"cmd": "why", "id": goal})
fresh_text = render_pretty("why", fresh)
check("why prints the floor left and the from-scratch floor, labelled",
      "serial floor left" in fresh_text and "from scratch" in fresh_text, fresh_text)
progressed = sim()
progressed.done.update(closure(NODES, goal) - {goal})
after = S._agent_dispatch(progressed, NODES, {"cmd": "why", "id": goal})
check("why floor left shrinks once the chain is built",
      after["critical_path_years_remaining"] < fresh["critical_path_years_remaining"]
      and after["critical_path_years"] == fresh["critical_path_years"],
      (after["critical_path_years_remaining"], fresh["critical_path_years_remaining"]))
