"""Step replies carry a short ALERTS block, capped and shown first on the step screen. The alert lines and the step screen are
called on events the test builds. The per-year hook is in test_step_progress_hook."""
from sim.ui.proto.step_alerts import step_alerts, alert_lines
from sim.ui.proto import render_screen_step as _render_big

from .harness import check

QUICK_TOPIC = True

events = [{"year": 101, "message": "CREDIT EXHAUSTED: 3 projects stopped", "event_kind": "credit_exhausted"},
          {"year": 102, "message": "a site is sacked: the library scrolls burn", "event_kind": "site_sacked"},
          {"year": 102, "message": "something harmless happened"}]
alerts = step_alerts(events=events, lost=[{"name": "Aqueduct", "year": 102}],
                     closed_concerns=["Sand filter"], founder_died=None,
                     goal_year=None, stopped_early=None, population_change=-0.4)
joined = " | ".join(alerts)
# presentation: what the alert lines name
check("alerts name credit, sacking, loss, closure and population collapse, not harmless events",
      "CREDIT EXHAUSTED" in joined and "sacked" in joined and "Aqueduct" in joined
      and "Sand filter" in joined and "population" in joined.lower() and "harmless" not in joined, alerts)
check("alerts are capped and short",
      len(step_alerts(events=[{"year": year, "message": "CREDIT EXHAUSTED %d" % year, "event_kind": "credit_exhausted"} for year in range(40)],
                      lost=[], closed_concerns=[], founder_died=None, goal_year=None,
                      stopped_early=None, population_change=0.0)) <= 8)
shown = _render_big.render_step(dict(ok=True, completed=[], events=[], lost=[], year=103, alerts=alerts))
check("the step screen puts ALERTS first, within the first lines",
      shown.splitlines()[0] == alert_lines(alerts)[0] and "ALERTS" in shown.splitlines()[0], shown[:200])
