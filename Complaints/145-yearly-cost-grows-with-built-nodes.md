# Each simulated year gets slower as more is built

**Status:** open

Once the economy takes off, the cost of simulating one year grows with the
number of completed nodes and running concerns. A default optimiser run for
Rome now reaches well over a thousand nodes within a century and a half, and
the late years take far longer than the early ones, so the long slow checks
(`early_playtest`, `determinism`, `run_reproducibility`,
`people_attrition_scholars`) take hours instead of minutes.

Measure with a profile of a long run, e.g.

    python3 -m cProfile -s cumulative sim/simulator.py run --civ rome_100ad --seed 1

and compare time per simulated year early and late.

## What it would take

Find the per-year passes that scan every node or concern (diffusion, adoption,
imitation candidates, capacity and revenue sums, fog checks) and make them
incremental or cached on what changed, keeping results identical
(`sim/perf_fingerprint.py`, determinism tests). Then decide whether the
slow checks need 200 simulated years or can prove the same property in fewer.
