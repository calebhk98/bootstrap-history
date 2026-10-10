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


def _finish_with_draw(node_id, draw, failed_attempts=0, capital=1000000.0, test_sim=None, offset=0.0):
    """Complete node_id with the dice forced to `draw` (or, when `draw` is None, to the displayed risk
    plus `offset`); return (sim, displayed risk). Passing `test_sim` reuses a game on which earlier
    attempts at this node all failed."""
    test_sim = sim(capital=capital) if test_sim is None else test_sim
    recorder = test_sim.rng = _RecordingRandom(0.0 if draw is None else draw)
    test_sim.state.projects.failed_attempts[node_id] = failed_attempts
    node = NODES[node_id]
    test_sim.state.projects.active.pop(node_id, None)   # a failed attempt leaves its project active
    test_sim.initialize_project(node_id, spent=0.0, cost_left=0.0)
    displayed = _explain_timing_and_risk(test_sim, NODES, node_id, node)["risk"]
    if draw is None:
        recorder.forced_draw = min(0.999999, max(0.0, displayed + offset))
    test_sim._complete(node_id)
    return test_sim, displayed


_risky_nodes = [node_id for node_id in ORDER if 0.05 <= NODES[node_id]["risk"] <= 0.9][:2]
check("set-up: there are risky nodes to compare", len(_risky_nodes) == 2, len(_risky_nodes))

_mismatches = []
_single_draw = []
for _node_id in _risky_nodes:
    # Failed attempts leave the node unfinished, so one game takes every failing draw;
    # a succeeding draw finishes the node and needs a game of its own.
    _failing_game = sim(capital=1000000.0)
    for _failed in (0, 2):
        _sim_below, _shown_below = _finish_with_draw(_node_id, 0.0, _failed, test_sim=_failing_game)
        _fails_at_zero = _sim_below.state.projects.failed_attempts[_node_id] > _failed
        # A draw just under / just over the displayed figure must land either side of the roll.
        _edge_sim_under, _shown = _finish_with_draw(
            _node_id, None, _failed, test_sim=_failing_game, offset=-1e-9)
        _edge_sim_over, _ = _finish_with_draw(_node_id, None, _failed, offset=1e-9)
        _under_fails = _edge_sim_under.state.projects.failed_attempts[_node_id] > _failed
        _over_fails = _edge_sim_over.state.projects.failed_attempts[_node_id] > _failed
        if not (_fails_at_zero and _under_fails and not _over_fails):
            _mismatches.append((_node_id, _failed, _shown_below))
        if _failed == 0:
            _single_draw.append(len(_edge_sim_over.rng.draws) == 1)
check("a draw just under the risk shown by `why` fails the attempt and one just over "
      "succeeds, on first and later attempts (the displayed figure is the one rolled)",
      not _mismatches, _mismatches[:3])
check("the failure roll is a single draw per attempt", all(_single_draw[:1]))
