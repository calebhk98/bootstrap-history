"""Complaint 320, general guard: stepping a game that is saved and loaded at a
year gives the same year as stepping the unbroken game, at every year of a
short run. Compares the digest the performance fingerprint uses, so any state
the next year reads but the save does not carry shows up as a different digest.
A defect that only shows once the economy is large is outside this short run;
`sim/perf_fingerprint.py` with a long scenario is where those are found."""
from .harness import *  # noqa: F401,F403
from sim import perf_fingerprint
from sim.engine.saveload import save_state, load_state

SCENARIO = dict(civ="rome_100ad", seed=1, years=40, events=True, fog=False)
unbroken = perf_fingerprint.build(SCENARIO)
save_path = os.path.join(tempfile.mkdtemp(), "save.json")
diverging_years = []
for year in range(1, SCENARIO["years"] + 1):
    save_state(unbroken, save_path)
    resumed = perf_fingerprint.build(SCENARIO)
    load_state(resumed, save_path)
    unbroken.step()
    resumed.step()
    if (perf_fingerprint.digest(perf_fingerprint.state_of(unbroken))
            != perf_fingerprint.digest(perf_fingerprint.state_of(resumed))):
        diverging_years.append(year)
check("a game saved and loaded before each year of a short run plays that year as the unbroken game does",
      not diverging_years, "years that differ: %s" % diverging_years)
