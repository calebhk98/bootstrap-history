"""knowledge_loss_warning: regression checks, run individually with `--only knowledge_loss_warning`."""
from .harness import *  # noqa: F401,F403
from sim.engine.data import closure
from sim.engine.knowledge_warning import knowledge_loss_warning
from sim.ui.proto.render_typed import render_pretty as _render_pretty

def _with_built_technologies(test_sim):
    """Give the sim technologies it built itself (not granted), so a sack has something to take."""
    test_sim.done.update([node_id for node_id in ORDER if node_id not in test_sim.done][:40])
    test_sim._done_changed()
    return test_sim


_far = _with_built_technologies(sim(civ="rome_100ad"))
_far.year = 100
check("no escalated warning while the sacking window is decades away",
      knowledge_loss_warning(_far) is None, knowledge_loss_warning(_far))

_near = _with_built_technologies(sim(civ="rome_100ad"))
_near.year = 210
_warning = knowledge_loss_warning(_near)
check("within thirty years of a sacking window the warning exists and names the window",
      _warning is not None and _warning["years"][0] == 235
      and _warning["years_until"] == 25, _warning)
_risk = _near.knowledge_risk()
check("it quotes risk's own expected loss per sacking",
      _warning["expected_technologies_lost_per_sacking"]
      == _risk["expected_technologies_lost_per_sacking"], (_warning, _risk))
_hedge = _warning["cheapest_hedge"]
check("it names the cheapest hedge with cost and steps away, found from the hedge table",
      _hedge["id"] in (tier[0] for tier in _near.corpus_hedge_tiers())
      and _hedge["steps_away"] >= 1 and _hedge["cost"] > 0, _hedge)
check("the hedge's steps are the unbuilt nodes in its closure",
      _hedge["steps_away"] == len(closure(NODES, _hedge["id"]) - _near.done), _hedge)

_now = _with_built_technologies(sim(civ="rome_100ad"))
_now.year = 240
_warning_now = knowledge_loss_warning(_now)
check("a window running now is flagged as in progress",
      _warning_now and _warning_now["in_progress"] and _warning_now["years_until"] == 0,
      _warning_now)

_hedged = _with_built_technologies(sim(civ="rome_100ad"))
_hedged.year = 210
_hedged.done.update(closure(NODES, "corpus_dispersed"))
_hedged._done_changed()
check("fully hedged: no cheaper hedge to name, no warning",
      knowledge_loss_warning(_hedged) is None, knowledge_loss_warning(_hedged))

_state = S._agent_dispatch(_near, NODES, {"cmd": "state"})
check("state carries the warning", _state.get("knowledge_loss_warning") == _warning,
      _state.get("knowledge_loss_warning"))
_state_text = _render_pretty("state", _state)
check("state text has a prominent warning line naming the window and the hedge",
      "WARNING" in _state_text and "235" in _state_text and _hedge["id"] in _state_text,
      _state_text[-900:])
_path = S._agent_dispatch(_near, NODES, {"cmd": "path", "id": GOAL})
check("path carries the warning and prints it",
      _path.get("knowledge_loss_warning") == _warning
      and "WARNING" in _render_pretty("path", _path) and "235" in _render_pretty("path", _path),
      _path.get("knowledge_loss_warning"))
_far_state = S._agent_dispatch(_far, NODES, {"cmd": "state"})
_unbuilt = sim(civ="rome_100ad")
_unbuilt.year = 210
check("nothing built by you means nothing to lose, so no warning",
      knowledge_loss_warning(_unbuilt) is None, knowledge_loss_warning(_unbuilt))
check("far from any window, state has no warning field",
      "knowledge_loss_warning" not in _far_state, _far_state.get("knowledge_loss_warning"))
