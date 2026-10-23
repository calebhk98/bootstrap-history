"""A project underfunded by arrears says so: in the log and on `why`, `stuck` and `portfolio`.

The screens print what the project's state carries (checked on built replies) and the log kind is a failure. The three
replies read off a game whose project carries the funding rule's verdict are the scenario in
test_arrears_visibility_scenario."""

QUICK_TOPIC = True
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

