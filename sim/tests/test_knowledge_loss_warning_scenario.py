"""Scenarios (Complaint 640; the rules are in test_knowledge_loss_warning): the warning reaches the `state` and
`path` replies on a whole game."""
from .harness import *  # noqa: F401,F403
from sim.engine.knowledge_warning import knowledge_loss_warning


def _with_built_technologies(test_sim):
    """Give the sim technologies it built itself (not granted), so a sack has something to take."""
    test_sim.done.update([node_id for node_id in ORDER if node_id not in test_sim.done][:40])
    test_sim._done_changed()
    return test_sim


# the first window that sacks a site as `risk` reports it; the years below are offsets from its start
_probe = _with_built_technologies(unopened_sim(civ="rome_100ad"))
_probe.year = 100
WINDOW_START = next(row["years"][0] for row in _probe.knowledge_risk()["known_hazards_ahead"] if row["sacks_a_site"])

_far = _with_built_technologies(unopened_sim(civ="rome_100ad"))
_far.year = WINDOW_START - 135
_near = _with_built_technologies(unopened_sim(civ="rome_100ad"))
_near.year = WINDOW_START - 25
_warning = knowledge_loss_warning(_near)

_state = S._agent_dispatch(_near, NODES, {"cmd": "state"})
check("state carries the warning", _state.get("knowledge_loss_warning") == _warning,
      _state.get("knowledge_loss_warning"))
_path = S._agent_dispatch(_near, NODES, {"cmd": "path", "id": GOAL})
check("path carries the warning",
      _path.get("knowledge_loss_warning") == _warning,
      _path.get("knowledge_loss_warning"))
_far_state = S._agent_dispatch(_far, NODES, {"cmd": "state"})
check("far from any window, state has no warning field",
      "knowledge_loss_warning" not in _far_state, _far_state.get("knowledge_loss_warning"))
