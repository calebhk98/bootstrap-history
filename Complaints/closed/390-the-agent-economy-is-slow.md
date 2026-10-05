# The agent economy makes games and the suite slow

**Status:** closed - folded into 181

With the agent economy on, a long Rome or Han game and the full test suite cost several times the CPU they did on the old economy. The hidden spin-up is slow the first time a civilisation opens after any change to `sim/`, because its cache is keyed on the source.

Measure with `python3 -m sim.tests.fingerprint check baseline_full.json` (CPU time per scenario) and `python3 -m sim.tests` (slowest checks), and per-phase with `python3 sim/economy_timing.py` (script since removed; recover with `git show 97473f1:sim/economy_timing.py`).

Candidates: the goods clearing per (good, area), household orders per cohort, entry's per-market recipe scan, and the spin-up length.
