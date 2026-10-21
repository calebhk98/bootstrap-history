"""Complaint 79 through a game: a standing shortage rides on the `state` reply and the state screen prints it as a
block. The shortage rules are in test_report_noise."""
from .harness import *  # noqa: F401,F403
from sim.engine import shortage_conditions
from sim.ui.protocol import _agent_dispatch
from sim.ui.proto.render_screen_state import render_state

game = sim()
shortage_conditions.note_shortage(game, "charcoal", 0.46)
state_reply = _agent_dispatch(game, NODES, {"cmd": "state"})
check("state carries the standing conditions", bool(state_reply.get("conditions")), list(state_reply)[:10])
# presentation: the state screen prints the standing condition as a block
check("the state screen prints them as a block",
      "CHARCOAL" in render_state(state_reply).upper() and "46%" in render_state(state_reply))
