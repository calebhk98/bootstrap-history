"""Scenarios (Complaints 145, 154 and 640): the `why` reply of a played game carries the specialist foreman `open` will
demand and a serial floor that counts only what is still unbuilt. The rules are in
test_why_foreman_and_remaining_floor."""
from .harness import *  # noqa: F401,F403

GOAL_NODE = "point_contact_transistor"

game = unopened_sim()
foreman_node = next(node_id for node_id in sorted(NODES) if game.venture_foreman(node_id)[0] is not None)
trade, share = game.venture_foreman(foreman_node)
why_out = S._agent_dispatch(game, NODES, {"cmd": "why", "id": foreman_node})
foreman = why_out.get("specialist_foreman_to_keep_it_open") or {}
check("why carries the specialist foreman trade and share open enforces",
      trade is not None and foreman.get("trade") == trade and abs(foreman.get("fte", -1.0) - share) < 0.01,
      (trade, share, foreman))

fresh = S._agent_dispatch(unopened_sim(), NODES, {"cmd": "why", "id": GOAL_NODE})
progressed = unopened_sim()
progressed.done.update(S.closure(NODES, GOAL_NODE) - {GOAL_NODE})
after = S._agent_dispatch(progressed, NODES, {"cmd": "why", "id": GOAL_NODE})
check("why floor left shrinks once the chain is built",
      after["critical_path_years_remaining"] < fresh["critical_path_years_remaining"]
      and after["critical_path_years"] == fresh["critical_path_years"],
      (after["critical_path_years_remaining"], fresh["critical_path_years_remaining"]))
