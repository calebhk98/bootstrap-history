"""score_literacy_percent: regression checks, run with `--only score_literacy_percent`."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_typed import render_pretty as _render_pretty

_game = sim()
_game.civ["literacy_general"] = 0.0749
_game.civ["literacy_elite"] = 0.9
_reply = S._agent_dispatch(_game, NODES, {"cmd": "score"})
_text = _render_pretty("score", _reply)
_line = next(line for line in _text.splitlines() if line.strip().startswith("literacy"))
_detail = _reply["components"]["literacy"]["raw_detail"]
check("score prints general literacy as a percentage, not a raw fraction",
      "7.49%" in _line, _line)
check("score prints the literacy figure against its ceiling",
      "%.2f%%" % (_detail["general_ceiling"] * 100) in _line, (_line, _detail))
