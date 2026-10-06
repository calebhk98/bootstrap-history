"""Complaint 320, general guard: stepping a game that is saved and loaded at a
year gives the same year as stepping the unbroken game, at each year of a run.
Compares the digest the performance fingerprint uses, so any state the next year
reads but the save does not carry shows up as a different digest. The quick run
is two years; the slow run is long enough to finish projects, admit firms and
meet hazards. A defect that only shows once the economy is large is found by
`sim/tests/fingerprint.py` with a long scenario."""
from .harness import *  # noqa: F401,F403
from sim.tests import fingerprint as perf_fingerprint
from sim.engine.saveload import save_state, load_state

QUICK_YEARS = 2
SLOW_YEARS = 12


def years_that_diverge(years):
    scenario = dict(civ="rome_100ad", seed=1, years=years, events=True, fog=False)
    unbroken = perf_fingerprint.build(scenario)
    save_path = os.path.join(tempfile.mkdtemp(), "save.json")
    diverging_years = []
    for year in range(1, years + 1):
        save_state(unbroken, save_path)
        resumed = perf_fingerprint.build(scenario)
        load_state(resumed, save_path)
        unbroken.step()
        resumed.step()
        if (perf_fingerprint.digest(perf_fingerprint.state_of(unbroken))
                != perf_fingerprint.digest(perf_fingerprint.state_of(resumed))):
            diverging_years.append(year)
    return diverging_years


quick_diverging = years_that_diverge(QUICK_YEARS)
check("a game saved and loaded before each year of a short run plays that year as the unbroken game does",
      not quick_diverging, "years that differ: %s" % quick_diverging)
slow_check("...and the same over a run long enough to finish projects, admit firms and meet hazards",
           lambda: (not years_that_diverge(SLOW_YEARS), "a year differs within %d years" % SLOW_YEARS))
