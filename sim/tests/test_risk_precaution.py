"""Complaint 120: money can buy a lower chance of failing, at a stated cost.

A node declaring the `precaution` mechanic quotes what a pilot plant or a
redundant team costs and what it does to the failure chance; starting with it
adds that cost and those hours to the project and lowers the dice's chance.
"""
from .harness import *  # noqa: F401,F403

NODE_ID = "cap_heat_1600"
SPEC = NODES[NODE_ID]["mechanics"]["precaution"]
UNOFFERED = "cap_tol_1mm"


def _fresh():
    test_sim = sim(capital=10000000.0)
    test_sim.start_refusal = lambda node_id: None   # staff and prerequisites are not under test
    return test_sim


check("set-up: the node offers a precaution and its risk is above zero",
      SPEC["cost_share"] > 0 and NODES[NODE_ID]["risk"] > 0)
check("a node that declares none quotes none", _fresh().precaution_quote(UNOFFERED) is None)

_quote = _fresh().precaution_quote(NODE_ID)
check("the quote names what is bought", _quote["label"] == SPEC["label"], _quote)
check("the quote shows a cost", _quote["extra_cost"] > 0, _quote)
check("the quote shows the extra hours", _quote["extra_founder_hours"] > 0, _quote)
check("the quote shows a lower chance with the lever than without",
      _quote["chance_of_failure_with"] < _quote["chance_of_failure_without"], _quote)
check("without the lever the chance is the ordinary one",
      abs(_quote["chance_of_failure_without"] - _fresh().effective_risk(NODE_ID)) < 1e-12)
check("the lever never makes the work safe", _quote["chance_of_failure_with"] > 0, _quote)

_plain = _fresh()
_bought = _fresh()
_plain_ok, _plain_why = _plain.start_project(NODE_ID)
_bought_ok, _bought_why = _bought.start_project(NODE_ID, precaution=True)
check("both starts went ahead", _plain_ok and _bought_ok, (_plain_why, _bought_why))
_plain_record = _plain.state.projects.active[NODE_ID]
_bought_record = _bought.state.projects.active[NODE_ID]
check("the bought project carries a larger bill",
      _bought_record["bill"] > _plain_record["bill"] + 1.0, (_bought_record["bill"], _plain_record["bill"]))
check("the bill grew by the quoted cost",
      abs(_bought_record["bill"] - _plain_record["bill"] - _quote["extra_cost"]) < 1.0)
check("the bought project needs more founder hours",
      _bought_record["ph_left"] > _plain_record["ph_left"] + 1.0)
check("the dice use the lowered chance once it is bought",
      _bought.effective_risk(NODE_ID) < _plain.effective_risk(NODE_ID) - 1e-6,
      (_bought.effective_risk(NODE_ID), _plain.effective_risk(NODE_ID)))
check("the quote after starting agrees with the lowered chance",
      abs(_bought.effective_risk(NODE_ID) - _quote["chance_of_failure_with"]) < 1e-12)

_refused_ok, _refused_why = _fresh().start_project(UNOFFERED, precaution=True)
check("buying a precaution a node does not offer is refused, and nothing starts",
      not _refused_ok and "offers no" in _refused_why, _refused_why)
