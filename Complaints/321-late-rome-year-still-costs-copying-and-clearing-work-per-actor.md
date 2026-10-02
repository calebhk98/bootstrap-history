# A late Rome year still spends most of its time pricing the same projects for every firm and re-solving the need clearing

**Status:** partly - one turn computes each project's material bill once for all firms, and the hiring ceiling of each trade once; a late Rome year (seed 1) is cheaper by the measure below. Still open: the founder-side phases of mid years (price solves per new gate set, `_compute_revenue_uncached` after every finished project), `final_demand`'s per-trial-price basket, and the founder's `venture_foremen_used` walk over every operating concern per opened venture

Profile of two Rome 100 AD seed 1 steps at about AD 250 (script: step once to warm, then `cProfile` two `Sim.step` calls; `sim/perf_fingerprint.py` builds the scenario). After the per-trade staff, category count, mining-technology and stock-sweep caches (Complaint 181), what remains by cumulative time:

- `Sim.project_material_bill` through `ActorWorld.copy_cost`, called by `imitation.copy_plan` for every firm's every missing chain step: the same node's bill is rebuilt for every firm in a year though it depends on the founder's world and not on the firm. A memo needs a key covering stock, market outcomes (which move with the actors' own supply and demand), freight and labour pressure, which actors change mid-turn, so it was not attempted without a way to prove it result-identical.
- `NeedDemandModel.final_demand` (sim/world): one price solve's clearing evaluates the whole household basket for each trial price although one material's price moves; only that material's need changes.
- A price solve (`prices.solved_prices`) in most late years, since each new set of techniques is a new gate set; the on-disk cache does not help a first run.
- `economy_production._compute_revenue_uncached` reruns after every finished project (the cache key includes the done-version), and walks every operating concern.

What it would take: a per-year table of the founder-side bill keyed on the registry's market version plus labour pressure; an incremental clearing; measure with the profile above and `perf_fingerprint.py check --quick`.

Measured after firm capacity scaling (Complaint 331): mean CPU of a Rome seed 1 year over years 141-150 went from 6.9 s to 6.6 s although the firm count fell from about 7600 to about 3100; the cost is not simply proportional to the count (price solves and the founder's own work dominate those years). Measure with a driver that steps the game and records `time.process_time()` per `Sim.step`.

Done: `sim/engine/view_share.py` keeps a table of answers for the view an actors' turn asks through (`SimWorld`), valid while the price table, the year's material demand and the actors' demand tally are the same objects and the actors' concern version, the year, built/operating versions, forest, nitre, population and the node's own stock are equal. It serves `project_material_bill` (through `copy_cost`) and the town's hiring ceiling before firms' staff (through `hiring_wage_per_hour`). Outside a view nothing is shared. Test: `sim/tests/test_complaint_321_shared_project_bills.py`. Measured on Rome seed 1 (save at year 250, then step; `cProfile` of two steps): bill computations per two years fell from about 95900 to about 5200 and the CPU of those two steps roughly halved; byte-identical per-year state digests over six late years against the code before. Note: a recompute of a market outcome has side effects on foreign trade state, so a cache that skips a recompute can change results; the stamp above kept the late years identical, and a new input to a bill must be added to it.

Re-measured 2026-10-02 after the goods market with firm sales (Rome seed 1, automation, years 50/100/150/200/250): well under a second of CPU per year, a flat profile. `solved_prices`, `_compute_revenue_uncached`, `final_demand` and `venture_foremen_used` each take about one percent or less of two mid or two late years, because the economy now stays at a few dozen firms in this run. The remains listed above are not fixed, only not costly at that size; no cache was added, since nothing measurable would be saved and the result could not be proved identical. Reopen the work with a profile of a run with thousands of firms.

Related: 304.

Owner decision (2026-10-02): before caching anything, find out whether it is impossible to speed up or whether the code uses poor algorithms, wasteful or repeated calculations. Expected to be largely resolved by the per-producer economic system.

Review (2026-10-02): with a rich founder a year is not cheap (2.5 to 3.6 s); the costs are repeated and algorithmic work, not missing caches. See `Complaints/reports/caching-and-algorithms-review.md` for the ranked changes.
