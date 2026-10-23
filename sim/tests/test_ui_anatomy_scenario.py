"""Scenarios (Complaint 69 and 640): the `anatomy` command on one played game. The rules are in test_ui_anatomy."""
from .harness import *  # noqa: F401,F403

game = unopened_sim()
_measured = sorted(node_id for node_id, node in NODES.items()
                   if (node.get("win_condition") or {}).get("metric") == "literacy_general")


def _ask(**fields):
    return S._agent_dispatch(game, NODES, dict(cmd="anatomy", **fields))


game.goal = _measured[0]
reply = _ask()
check("a literacy goal gives an anatomy with a target, current value and gap in a played game",
      reply.get("ok") and reply["metric"] == "literacy_general" and reply["target"]["gap"] is not None
      and reply["current"] is not None and not reply["generic"], reply)
check("the literacy anatomy's current value is the education screen's number",
      reply["current"] == S._agent_dispatch(game, NODES, {"cmd": "education"})["literacy"]["general"], reply["current"])
game.goal = GOAL
check("a research goal in a played game is pointed to path and leverage", _ask().get("research_goal") is True)

game.goal = _measured[0]
game.fog = True
_fogged = _ask()
check("under fog, a goal that is not in view is refused with a cause in a played game",
      _fogged.get("ok") is False and _fogged.get("cause") == "goal_out_of_view", _fogged)
game.fog = False
