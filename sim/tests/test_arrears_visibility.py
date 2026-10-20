"""A project underfunded by arrears says so: in the log and on `why`, `stuck` and `portfolio`.

The screens print what the project's state carries (checked on built replies); the log kind is a failure; one
named scenario runs a year in arrears and reads the log line and the three replies off the game."""
from .harness import *  # noqa: F401,F403
from sim.refusal import LogLine, cause_of, facts_of
from sim.engine import project_funding
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

# --- scenario: a project underfunded by arrears is named in the log and on the three screens a player reads
s = sim(capital=1000.0)
_af_k = next(node_id for node_id in NODES
             if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 500)
_af_n = NODES[_af_k]
s.active[_af_k] = dict(ph_left=float(_af_n["ph"]), yrs=0.0, spent=0.0,
                       cost_left=s.project_cost(_af_k), lab_left=dict(_af_n["lab"]))
_lim_af = s.credit_limit()
_fixed_af = s.living_cost() + s.upkeep() + s.mine_operating_cost()
_reserve_af = max(0.0, _fixed_af - s.revenue())
# Deep enough that the project's own purse is negative (50 short), but inside the credit limit; a deeper debt
# costs interest at the market rate, and at a high rate one year's alone could carry the household past the limit.
s.capital = min(-1.0, _reserve_af - 0.6 * _lim_af - 50.0)
_before_log = len(s.log)
s.step()
_new_lines = [message for _, message in s.log[_before_log:]]
_progress = s.active.get(_af_k, {})
_port = S._agent_dispatch(s, NODES, {"cmd": "portfolio"})
_port_row = next((row for row in _port.get("projects", []) if row["id"] == _af_k), {})
_why = S._agent_dispatch(s, NODES, {"cmd": "why", "id": _af_k})
_stuck = S._agent_dispatch(s, NODES, {"cmd": "stuck"})
_stuck_reason = next((reason for reason in _stuck.get("what_is_holding_you_up", []) if reason.get("what") == "work in hand"), {})
check("scenario: the year a project is underfunded by arrears, the log names the hours lost, and `why`, `stuck` and "
      "`portfolio` carry the cause against that project while founder hours are plentiful and idle",
      _progress.get("underfunded_this_year") is True
      and any(cause_of(message) == "arrears_hours_lost" and _af_k in facts_of(message)["projects"] for message in _new_lines)
      and (_port.get("founder_hours_available_this_year") or 0) > 1000
      and "arrears" in (_port_row.get("why_underfunded") or "")
      and _why.get("waiting_on_kind") == "founder_hours" and "arrears" in (_why.get("why_underfunded") or "")
      and "arrears" in ((_stuck_reason.get("each_why_underfunded") or {}).get(_af_k) or ""),
      (_progress.get("why_underfunded"), _new_lines, _port_row.get("why_underfunded"), _why.get("why_underfunded"),
       _stuck_reason.get("each_why_underfunded")))
