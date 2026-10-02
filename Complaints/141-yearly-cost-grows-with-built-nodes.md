# Each simulated year gets slower as more is built

**Status:** partly - firm imitation scan, `rivals_of`, the material-demand and price-table lookups and settlement summaries no longer rescan everything per call; a year at ~1,800 built nodes fell from roughly 17-23 s to 3-4 s with prices cached (`python3 /path/solves-style loop over a saved game`; the 135-year Rome seed 1 run went from 108 s to 24 s of CPU with the price cache warm). Later: the production catalog lookup resolved filesystem paths on every call (nearly a million a 150-year Rome run) and every market clearing asked every actor's every concern about every material; both are now an indexed lookup (`python3 sim/perf_fingerprint.py check --quick` identical), and the slow checks `determinism` and `run_reproducibility` use short horizons (the scholar-wall check could not be shortened, Complaint 280). A rich Rome run (default capital, optimiser, no events) costs about a quarter of what it did to year 106; its years past 100 are still the slow ones (cold price solves and per-firm copy plans). Remaining: the per-actor per-material supply walk (Complaint 304), a cold price solve is several seconds per unseen technology set and a year can need two or three; the flat remainder is per-project throttle, wage and revenue recomputation (`resource_throttle`, `annual_wage`, `revenue`), `_standing_material_terms` rebuilt on every completion, and `consider_entry`'s copy plans.

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

Related: 181, 321.
