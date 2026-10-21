"""Complaint 120, through a running game: starting a project with the precaution adds the quoted cost and hours to it
and lowers the dice's chance; buying one a node does not offer is refused and starts nothing. The rules are in
test_risk_precaution."""
from .harness import *  # noqa: F401,F403

NODE_ID = "cap_heat_1600"
UNOFFERED = "cap_tol_1mm"


def _fresh():
    test_sim = sim(capital=10000000.0)
    test_sim.start_refusal = lambda node_id: None   # staff and prerequisites are not under test
    test_sim.state.projects.done.update(NODES[NODE_ID]["pre"])   # the shared research gate still reads what is known
    test_sim._done_changed()
    test_sim.labour.craft_hands_available = lambda: 1.0e6   # nor is how many hands the shared gate counts
    test_sim.labour.scholar_hands_available = lambda: 1.0e6
    return test_sim


_quote = _fresh().precaution_quote(NODE_ID)
_plain = _fresh()
_bought = _fresh()
_plain_ok, _plain_why = _plain.start_project(NODE_ID)
_bought_ok, _bought_why = _bought.start_project(NODE_ID, precaution=True)
check("both starts went ahead", _plain_ok and _bought_ok, (_plain_why, _bought_why))
_plain_record = _plain.state.projects.active[NODE_ID]
_bought_record = _bought.state.projects.active[NODE_ID]
check("the bought project's bill grew by the quoted cost and its founder hours by the quoted hours",
      abs(_bought_record["bill"] - _plain_record["bill"] - _quote["extra_cost"]) < 1.0
      and abs(_bought_record["ph_left"] - _plain_record["ph_left"] - _quote["extra_founder_hours"]) < 1.0,
      (_bought_record["bill"], _plain_record["bill"], _quote))
check("the dice use the lowered chance once it is bought, as quoted",
      _bought.effective_risk(NODE_ID) < _plain.effective_risk(NODE_ID) - 1e-6
      and abs(_bought.effective_risk(NODE_ID) - _quote["chance_of_failure_with"]) < 1e-12,
      (_bought.effective_risk(NODE_ID), _plain.effective_risk(NODE_ID)))

_refused_game = _fresh()
_refused_ok, _refused_why = _refused_game.start_project(UNOFFERED, precaution=True)
_refused_reply = S._agent_dispatch(_refused_game, NODES, {"cmd": "start", "id": UNOFFERED, "precaution": True})
check("buying a precaution a node does not offer is refused, and nothing starts",
      not _refused_ok and not _refused_reply["ok"] and UNOFFERED not in _refused_game.active
      and _refused_game.precaution_quote(UNOFFERED) is None, _refused_why)
