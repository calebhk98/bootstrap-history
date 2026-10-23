"""SCENARIO (arrears visibility): in a whole game a project the funding rule left underfunded by arrears carries the cause on
`why`, `stuck` and `portfolio` while founder hours are plentiful and idle. The screens and the log kind are in
test_arrears_visibility."""
from .harness import *  # noqa: F401,F403
from sim.engine import project_funding
_reason = project_funding.WHY_IN_ARREARS

# --- the replies a player reads carry the cause a project was left with by the funding rule. The project is
# put in the state the yearly step leaves it in (`fund_year`'s verdict), not run through the step: a founder who
# commits hours to a project loses standing income and with it the credit line, so a year in arrears ends in
# CREDIT EXHAUSTED and the project is dropped before the replies could be read.
s = unopened_sim(capital=1000.0)
_af_k = next(node_id for node_id in NODES
             if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n = NODES[_af_k]
_verdict = project_funding.fund_year(400.0, -100.0, 500.0, 0.0, 500.0, True)
s.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0, spent=0.0,
                       cost_left=s.project_cost(_af_k), lab_left=dict(_af_n["lab"]),
                       underfunded_this_year=_verdict.underfunded, why_underfunded=_verdict.why)
_port = S._agent_dispatch(s, NODES, {"cmd": "portfolio"})
_port_row = next((row for row in _port.get("projects", []) if row["id"] == _af_k), {})
_why = S._agent_dispatch(s, NODES, {"cmd": "why", "id": _af_k})
_stuck = S._agent_dispatch(s, NODES, {"cmd": "stuck"})
_stuck_reason = next((reason for reason in _stuck.get("what_is_holding_you_up", []) if reason.get("what") == "work in hand"), {})
check("scenario: a project the funding rule left underfunded by arrears carries the cause on `why`, `stuck` and "
      "`portfolio` while founder hours are plentiful and idle",
      _verdict.why == project_funding.WHY_IN_ARREARS
      and _port_row.get("why_underfunded") == _verdict.why
      and _why.get("waiting_on_kind") == "founder_hours" and _why.get("why_underfunded") == _verdict.why
      and (_stuck_reason.get("each_why_underfunded") or {}).get(_af_k) == _verdict.why,
      (_port_row.get("why_underfunded"), _why.get("why_underfunded"), _stuck_reason.get("each_why_underfunded")))
