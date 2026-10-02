"""Complaint 274: a failure you cannot measure teaches nothing, and says so.

A node that declares `diagnosis_instrument` lets its failures improve the
retry odds only when the instrument is held; the failure report names the
figure needed and, without the instrument, which instrument would measure it.
"""
from .harness import *  # noqa: F401,F403
from sim.engine.data import closure
from sim.engine.projects_completion import FAILED_PREFIX

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


def _last_failure_text(test_sim):
    return [text for _year, text in test_sim.state.household.log if FAILED_PREFIX in text][-1]


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
_blind_text = _last_failure_text(_blind)
check("the blind failure names the instrument that would have measured it",
      NODES[INSTRUMENT]["name"] in _blind_text, _blind_text)
check("the blind failure states the figure the work needed",
      SPEC["needed_words"] in _blind_text, _blind_text)
check("the blind failure says it cannot be diagnosed", "cannot" in _blind_text, _blind_text)
_equipped_text = _last_failure_text(_equipped)
check("the equipped failure reports what was reached against what was needed",
      SPEC["needed_words"] in _equipped_text and "reached" in _equipped_text, _equipped_text)
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
