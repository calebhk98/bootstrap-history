"""Complaint 320, general guard: stepping a game that is saved and loaded at a
year gives the same year as stepping the unbroken game. Compares the digest the
performance fingerprint uses, so any state the next year reads but the save does
not carry shows up as a different digest. The game is saved after one played year
(so it carries a year of accumulated state), resumed in a fresh build and both are
played one more year. A defect that only shows once the economy is large is found
by `sim/tests/fingerprint.py` with a long scenario."""
from .harness import *  # noqa: F401,F403
from sim.tests import fingerprint as perf_fingerprint
from sim.engine.saveload import save_state, load_state

SCENARIO = dict(civ="rome_100ad", seed=1, years=2, events=True, fog=False)


def _resumed_year_differs():
    unbroken = perf_fingerprint.build(SCENARIO)
    unbroken.step()
    save_path = os.path.join(tempfile.mkdtemp(), "save.json")
    save_state(unbroken, save_path)
    resumed = perf_fingerprint.build(SCENARIO)
    load_state(resumed, save_path)
    unbroken.step()
    resumed.step()
    same = (perf_fingerprint.digest(perf_fingerprint.state_of(unbroken))
            == perf_fingerprint.digest(perf_fingerprint.state_of(resumed)))
    return same, "the resumed second year differs from the unbroken second year"


slow_check("a game saved and loaded after its first year plays the second year as the unbroken game does",
           _resumed_year_differs)
