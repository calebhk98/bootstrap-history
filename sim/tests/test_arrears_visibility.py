"""A project underfunded by arrears says so: in the log and on `why`, `stuck` and `portfolio`.

The screens print what the project's state carries (checked on built replies); the log kind is a failure; one
named scenario reads the three replies off a game whose project carries the funding rule's verdict."""
from .harness import *  # noqa: F401,F403
from sim.refusal import LogLine, cause_of, facts_of
from sim.engine import project_funding
from sim.engine.arrears_hours_line import arrears_hours_line
from sim.ui.proto import event_kinds, render_portfolio_rows, render_screen_why

_reason = project_funding.WHY_IN_ARREARS

# --- a fully-paid project, waiting only on the calendar, has no hours lost to arrears to report
check("a project that owes nothing further loses no hours to arrears, so the wasted-hours line is never raised for it",
      project_funding.fund_year(0.0, -5000.0, 400.0, 0.0, 500.0, True).hours_lost_to_arrears == 0.0)

# --- the log line is bad news, found by 'log failures'
check("a line of kind arrears_hours_lost is a failure, as every other arrears line is",
      event_kinds.is_failure(LogLine("arrears_hours_lost", "x", projects=["p"])))

# --- the screens print the cause the project carries
# presentation: the rendered screens print the stored cause
check("the portfolio row prints why_underfunded under the row's 'waiting on' line",
      _reason in " ".join(" ".join(line.split()) for line in render_portfolio_rows.project_lines(
          {"name": "Academy", "constraint": "founder_hours", "waiting_on": "your hours", "why_underfunded": _reason})),
      render_portfolio_rows.project_lines({"name": "Academy", "constraint": "founder_hours",
                                           "waiting_on": "your hours", "why_underfunded": _reason}))
# presentation: the rendered screens print the stored cause
check("the portfolio row prints no cause for a project that is not underfunded",
      not any("arrears" in line for line in render_portfolio_rows.project_lines(
          {"name": "Academy", "constraint": "founder_hours", "waiting_on": "your hours"})))
# presentation: the rendered screens print the stored cause
_why_lines = render_screen_why._why_status({"active": True, "waiting_on": "your hours", "why_underfunded": _reason})
check("the `why` screen prints why_underfunded for an active project, as well as what it waits on",
      "waiting on: your hours" in " ".join(" ".join(_why_lines).split()) and "arrears" in " ".join(_why_lines), _why_lines)
# presentation: the rendered screens print the stored cause
_stuck_text = _PROTO.render_stuck({"you_could_begin": 1, "and_could_pay_for": 0, "what_is_holding_you_up": [
    {"what": "work in hand", "each_waiting_on": {"academy": "your hours"}, "each_why_underfunded": {"academy": _reason}}]})
check("the `stuck` screen carries the cause beside the bare 'waiting on your hours' line",
      "waiting on your hours" in _stuck_text and "arrears" in _stuck_text, _stuck_text)

# --- the log line names the project and the hours it lost, as fields
_line = arrears_hours_line([("academy_network", 1750.0)])
check("the wasted-hours line is of kind arrears_hours_lost and carries the project and the hours as facts",
      cause_of(_line) == "arrears_hours_lost" and facts_of(_line)["projects"] == ["academy_network"]
      and facts_of(_line)["hours"] == 1750.0, facts_of(_line))

# --- the replies a player reads carry the cause a project was left with by the funding rule. The project is
# put in the state the yearly step leaves it in (`fund_year`'s verdict), not run through the step: a founder who
# commits hours to a project loses standing income and with it the credit line, so a year in arrears ends in
# CREDIT EXHAUSTED and the project is dropped before the replies could be read.
s = sim(capital=1000.0)
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
