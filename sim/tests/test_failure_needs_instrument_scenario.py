"""Scenario: Complaint 274 in a game. Two failed attempts at a node that declares `diagnosis_instrument` buy no risk learning
without the instrument and do lower the risk with it, and a node without the mechanic learns from every failure. The
rules (when a failure teaches, what the report says) are in test_failure_needs_instrument."""
from .harness import *  # noqa: F401,F403
from sim.engine.data import closure

NODE_ID = "cap_tol_1um"
SPEC = NODES[NODE_ID]["mechanics"]["diagnosis_instrument"]
INSTRUMENT = SPEC["instrument"]


class _Forced(random.Random):
    def __init__(self, draw):
        super().__init__(1)
        self.draw = draw

    def random(self):
        return self.draw


def _fail_twice(holds_instrument):
    test_sim = sim(capital=1000000.0)
    test_sim.rng = _Forced(0.0)
    if holds_instrument:
        test_sim.state.projects.done.add(INSTRUMENT)
    test_sim.initialize_project(NODE_ID, spent=0.0, cost_left=0.0)
    for _ in range(2):
        test_sim._complete(NODE_ID)
    return test_sim


check("set-up: the instrument is not a prerequisite, so it can be lacked",
      INSTRUMENT not in closure(NODES, NODE_ID))
_blind = _fail_twice(False)
_equipped = _fail_twice(True)
check("both attempts failed", _blind.state.projects.failed_attempts[NODE_ID] == 2
      and _equipped.state.projects.failed_attempts[NODE_ID] == 2)
check("without the instrument the failures buy no risk learning",
      abs(_blind.effective_risk(NODE_ID) - NODES[NODE_ID]["risk"]) < 1e-12,
      _blind.effective_risk(NODE_ID))
check("with the instrument the same failures do lower the risk",
      _equipped.effective_risk(NODE_ID) < NODES[NODE_ID]["risk"] - 1e-6,
      _equipped.effective_risk(NODE_ID))
_other = next(node_id for node_id in ORDER
              if "diagnosis_instrument" not in (NODES[node_id].get("mechanics") or {})
              and 0.1 < NODES[node_id]["risk"] < 0.9)
_plain = sim(capital=1000000.0)
_plain.rng = _Forced(0.0)
_plain.initialize_project(_other, spent=0.0, cost_left=0.0)
_plain._complete(_other)
_plain._complete(_other)
check("a node without the mechanic still learns from every failure",
      _plain.effective_risk(_other) < NODES[_other]["risk"] - 1e-6)
