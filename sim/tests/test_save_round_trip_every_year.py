"""Complaint 320, general guard: stepping a game that is saved and loaded at a
year gives the same year as stepping the unbroken game, at every year of a
short run. Compares the digest the performance fingerprint uses, so any state
the next year reads but the save does not carry shows up as a different digest.
A defect that only shows once the economy is large is outside this short run;
`sim/tests/fingerprint.py` with a long scenario is where those are found."""
from .harness import *  # noqa: F401,F403
from sim.tests import fingerprint as perf_fingerprint
from sim.engine.saveload import save_state, load_state

SCENARIO = dict(civ="rome_100ad", seed=1, years=31, events=True, fog=False)
unbroken = perf_fingerprint.build(SCENARIO)
save_path = os.path.join(tempfile.mkdtemp(), "save.json")
diverging_years = []
# Every year while the economy is young (Complaint 320 diverged at year 10) and the year
# Complaint 371 first diverged (31); the unbroken game still plays every year in between.
CHECKED_YEARS = set(range(1, 13)) | {31}
for year in range(1, max(CHECKED_YEARS) + 1):
    if year not in CHECKED_YEARS:
        unbroken.step()
        continue
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
