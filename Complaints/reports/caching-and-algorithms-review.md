# Caching against algorithms: a review for complaint 321

Read-only review, 2026-10-02. Profile: Rome 100 AD, seed 1, founder capital 1e8, two `Sim.step` calls under cProfile (scripts kept outside the repository). Mid game (about 158 operating concerns): 3.5 s for two years. About year 150: 7.2 s. About year 300 (62 operating): 5.0 s. Complaint 321's earlier "negligible" measure was for a run with a few dozen firms; a rich founder is not cheap.

## Caches that hide an algorithmic problem

- `economy_materials._done_memo`: answers keyed on a stamp flushed whenever `len(done)` changes. `concern_prices` is a pure function of the held set, which is already in its key, so the flush is needless.
- The household revenue cache (16-field key including `_done_ver`): revenue is a sum over operating concerns and is recomputed in full after every finished project to add one term.
- `prices._SOLVE_CACHE`: one solve per new gate set is inherent, but `priced_goods_table` (three solves plus `entries_in_reach`) has no memo of its own and runs about 100 times in two years.
- `view_share.py`: a hand-kept dependency stamp of about 12 versions; it exists because the same bill is rebuilt per firm.
- The per-year market and demand tallies (`_market_outcome_cache`, `_goods_offers_cache`, the demand caches): symptoms of the clearing being evaluated many times a year.

Version-keyed derived caches (techniques in use, material prices, freight distances) are mostly legitimate; the fragile part is the `_ver` plumbing. Static tree and data indexes and per-call scratch memos are fine.

## Where the time goes (about year 150)

- `revenue` / `_compute_revenue_uncached`, 2.8 s: repeated work. Invalidated after each finished project (59 times in two years), then walks about 460 concerns. Keep per-concern terms and recompute only those that changed.
- `concern_baskets_now` / `_concern_ratios`, 2.1 s: repeated. Pure in the held set, so about three distinct values would do.
- `priced_goods_table` and `calculated_goods_prices`, 2.0 s each: repeated at the same held set with no memo.
- `entries_in_reach`, `_unheld_steps_to`, `data.closure` (about 12,000 calls, 530,000 `hard_pre`): algorithmic waste. A full ancestor walk per production entry per call over a static tree. Precompute ancestor bitmasks once per tree; steps to a node become a count of `ancestors[node] & ~held`.
- `advance_actors`, `consider_entry`, `copy_plan`, about 1.5 s: the same node bills rebuilt per firm.
- `quote_annual` / `wage_cost_factors`, about 1.5 s: a per-trade rate, the same for every employer, recomputed per call.

## Ranked changes (effect measured on the 7.3 s sample)

1. Key `concern_prices` and `priced_goods_table` on the held set alone: about 2 s.
2. Incremental revenue (per-concern terms, only changed ones recomputed): about 2 s.
3. Ancestor bitmasks for `closure` and `_unheld_steps_to`: about 1.5 s.
4. A per-trade labour quote per year: about 0.8 s.
5. The per-producer market (complaint 375): removes the per-firm bill rebuild, `view_share` and its stamp, the repeated clearing and the demand tallies, about 2 to 3 s.

Caches that can then be deleted: the household revenue key, the `len(done)`-stamped memo, `view_share`, and the per-year offer and demand caches. Each one deleted removes a source of save/load and determinism bugs.
