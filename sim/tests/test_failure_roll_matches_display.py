"""failure_roll_matches_display: complaint 161, the risk shown is the risk rolled."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.techtree import _explain_timing_and_risk


class _RecordingRandom(random.Random):
    """Random source that logs every draw so a check can see what was rolled against."""

    def __init__(self, forced_draw):
        super().__init__(1)
        self.forced_draw = forced_draw
        self.draws = []

    def random(self):
        self.draws.append(self.forced_draw)
        return self.forced_draw


def _finish_with_draw(node_id, draw, failed_attempts=0, capital=1000000.0, test_sim=None):
    """Complete node_id with the dice forced to `draw`; return (sim, displayed risk).

    Pass a sim back in to reuse it for a draw that fails (the attempt stays
    active and is re-armed here); a draw that succeeds consumes its sim.
    The mechanism is the same on any civilisation, so the cheap norse one is used.
    """
    if test_sim is None:
        test_sim = sim("norse_900ad", capital=capital)
    test_sim.rng = _RecordingRandom(draw)
    test_sim.state.projects.failed_attempts[node_id] = failed_attempts
    test_sim.state.projects.active.pop(node_id, None)
    node = NODES[node_id]
    test_sim.initialize_project(node_id, spent=0.0, cost_left=0.0)
    displayed = _explain_timing_and_risk(test_sim, NODES, node_id, node)["risk"]
    test_sim._complete(node_id)
    return test_sim, displayed


_risky_nodes = [node_id for node_id in ORDER if 0.05 <= NODES[node_id]["risk"] <= 0.9][:12]
check("set-up: there are risky nodes to compare", len(_risky_nodes) >= 5, len(_risky_nodes))

_mismatches = []
for _node_id in _risky_nodes:
    _reused = None   # one sim serves every draw that fails; each success needs its own
    for _failed in (0, 2):
        _sim_below, _shown_below = _finish_with_draw(_node_id, 0.0, _failed, test_sim=_reused)
        _reused = _sim_below
        _sim_above, _shown_above = _finish_with_draw(_node_id, 0.999999, _failed)
        _fails_at_zero = _sim_below.state.projects.failed_attempts[_node_id] > _failed
        _fails_at_top = _sim_above.state.projects.failed_attempts[_node_id] > _failed
        # A draw just under / just over the displayed figure must land either side of the roll.
        _edge_sim_under, _shown = _finish_with_draw(
            _node_id, max(0.0, _shown_below - 1e-9), _failed, test_sim=_reused)
        _edge_sim_over, _ = _finish_with_draw(_node_id, min(0.999999, _shown_below + 1e-9), _failed)
        _under_fails = _edge_sim_under.state.projects.failed_attempts[_node_id] > _failed
        _over_fails = _edge_sim_over.state.projects.failed_attempts[_node_id] > _failed
        if not (_fails_at_zero and not _fails_at_top and _under_fails and not _over_fails):
            _mismatches.append((_node_id, _failed, _shown_below))
check("a draw just under the risk shown by `why` fails the attempt and one just over "
      "succeeds, on first and later attempts (the displayed figure is the one rolled)",
      not _mismatches, _mismatches[:3])
check("the failure roll is a single draw per attempt",
      all(len(_finish_with_draw(_node_id, 0.999999)[0].rng.draws) == 1 for _node_id in _risky_nodes[:3]))
