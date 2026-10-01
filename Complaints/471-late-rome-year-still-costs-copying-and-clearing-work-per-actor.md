# A late Rome year still spends most of its time pricing the same projects for every firm and re-solving the need clearing

**Status:** open

Profile of two Rome 100 AD seed 1 steps at about AD 250 (script: step once to warm, then `cProfile` two `Sim.step` calls; `sim/perf_fingerprint.py` builds the scenario). After the per-trade staff, category count, mining-technology and stock-sweep caches (Complaint 185), what remains by cumulative time:

- `Sim.project_material_bill` through `ActorWorld.copy_cost`, called by `imitation.copy_plan` for every firm's every missing chain step: the same node's bill is rebuilt for every firm in a year though it depends on the founder's world and not on the firm. A memo needs a key covering stock, market outcomes (which move with the actors' own supply and demand), freight and labour pressure, which actors change mid-turn, so it was not attempted without a way to prove it result-identical.
- `NeedDemandModel.final_demand` (sim/world): one price solve's clearing evaluates the whole household basket for each trial price although one material's price moves; only that material's need changes.
- A price solve (`prices.solved_prices`) in most late years, since each new set of techniques is a new gate set; the on-disk cache does not help a first run.
- `economy_production._compute_revenue_uncached` reruns after every finished project (the cache key includes the done-version), and walks every operating concern.

What it would take: a per-year table of the founder-side bill keyed on the registry's market version plus labour pressure; an incremental clearing; measure with the profile above and `perf_fingerprint.py check --quick`.

Measured after firm capacity scaling (Complaint 550): mean CPU of a Rome seed 1 year over years 141-150 went from 6.9 s to 6.6 s although the firm count fell from about 7600 to about 3100; the cost is not simply proportional to the count (price solves and the founder's own work dominate those years). Measure with a driver that steps the game and records `time.process_time()` per `Sim.step`.
