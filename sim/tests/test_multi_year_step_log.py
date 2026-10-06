"""multi_year_step_log: `step N` logs and reports every simulated year.

Complaints/159: after `step 2` the log showed nothing for the second year.
Measured: the multi-year step logs exactly what N single steps log; the
"population still N% below trend" line is deliberately rate-limited, not
missing (its spacing is not tested here: it needs a long run).
"""
from .harness import *  # noqa: F401,F403


def _log_rows(test_sim):
    return [(year, message) for year, message in test_sim.log]


def _game():
    test_sim = sim(events=True)
    test_sim.end_year = test_sim.cfg["start_year"] + 200
    for node_id in ("tx2_bleaching_sun", "tx2_count_standard", "clock_mechanical_escapement"):
        test_sim.start_project(node_id)
    return test_sim


YEARS = 3
multi = _game()
multi_reply = S._agent_dispatch(multi, NODES, {"cmd": "step", "years": YEARS})
single = _game()
single_replies = [S._agent_dispatch(single, NODES, {"cmd": "step", "years": 1})
                  for _ in range(YEARS)]

check("step N leaves the same log as N single steps",
      _log_rows(multi) == _log_rows(single),
      (_log_rows(multi), _log_rows(single)))
check("step N ends in the same year as N single steps",
      multi_reply["year"] == single_replies[-1]["year"],
      (multi_reply["year"], single_replies[-1]["year"]))

single_events = [(row["year"], row["message"])
                 for reply in single_replies for row in reply["events"]]
multi_events = [(row["year"], row["message"]) for row in multi_reply["events"]]
check("step N reports the same events, from every year, as N single steps",
      multi_events == single_events, (multi_events, single_events))

logged_years = sorted({year for year, _ in _log_rows(multi) if year >= multi_reply["year"] - YEARS})
reported_years = sorted({year for year, _ in multi_events})
check("every year with a log entry inside the step appears in the step's events",
      all(year in reported_years for year in logged_years),
      (logged_years, reported_years))
printed = _RP("step", multi_reply)
check("the printed step report shows events of every reported year",
      all(("DURING %d" % year in printed) or ("COMPLETED %d" % year in printed)
          for year in reported_years),
      (reported_years, printed[:800]))
check("the step covers a second year that logged something, so the comparison is not about one year",
      len(reported_years) >= 2, reported_years)
