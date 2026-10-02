# Each market clearing sums every actor's concerns once per material

**Status:** open

A 150-year Rome run (seed 1) spends about a quarter of its CPU in `Sim.actor_supply`: `_market_conditions` runs tens of thousands of times a run (hundreds a year), and each call walks every actor and every concern the actor runs, building a fresh `SimWorld` view and re-reading the production index. Skipping concerns that do not make the material (complaint 141) removed the per-concern lookups but the per-actor, per-material walk remains. Han China 100 AD seed 1 is several times slower than the other fingerprint scenarios over 100 years; `python3 sim/perf_fingerprint.py record --quick x.json` prints the per-scenario CPU.

Why it matters: it is the largest remaining flat cost in a late year, and it grows with firms times materials.

What it would take: a supply table per year, kept by the actor registry and invalidated by the registry's concern version plus the year (ramp) and staffing changes, read per material; the founder's market code then asks the table instead of walking actors. Check with `perf_fingerprint.py check --quick`.

Measured again after complaint 321's shared table (Rome seed 1, two steps from year 250 of a play): `actor_supply` no longer shows among the top costs of a late year; firms are fewer than when this was filed (they expand instead of multiplying). Left open until a profile of a larger firm count shows the walk again.

Related: 181.

Owner decision (2026-10-02): important for speed.
