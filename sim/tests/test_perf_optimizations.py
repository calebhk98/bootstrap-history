"""Conservative performance optimizations: the fingerprint tool's quick scenarios cover the cases the speed-ups could
break. The boolean-only `start_reason` and the fingerprint's state toggle, which need a game, are in
test_perf_optimizations_scenario. (The afford gate's funding arithmetic is held by test_arrears_hours.)"""

QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.tests import fingerprint as F

scenarios = F.QUICK_SCENARIOS
check("perf_fingerprint QUICK_SCENARIOS names a Rome and a non-Rome start, with events and with fog, at least three",
      any(s["civ"] == "rome_100ad" for s in scenarios) and any(s["civ"] != "rome_100ad" for s in scenarios)
      and any(s["events"] for s in scenarios) and any(s["fog"] for s in scenarios) and len(scenarios) >= 3,
      scenarios)
