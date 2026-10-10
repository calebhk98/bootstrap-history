# Late-game performance: slow steps, slow `open`, growing save

**Status:** closed - a late Rome step (about AD 250, seed 1) is several times cheaper: actors' per-trade staff is a kept running sum instead of a recount per read, concerns are counted by category in one walk, mining technology and market standing are kept per built/operating state, the stock ledger sweeps only after a new key, the actors' demand tally skips firms (result-identical on `sim/tests/fingerprint.py check --quick`; what remains is filed as 321). Earlier: a command that changes nothing (refusals, a repeated `state`) no longer rewrites the save, saves are written compact through the C JSON encoder (a quarter smaller on the test fixture), and the per-year scans behind Complaint 141 are cheaper. A late save of a 150-year Rome run and a warm `available` measure well under a second each (profile script in the 145 history; a save is a fraction of a second CPU), so the remaining cost is the step. Closing notes (each item re-measured against the code):

- Price solve cache key: done. `solve_cache.environment_digest(source_modules=...)` hashes the data files and only the sim source the solver can import (`prices._SOLVER_SOURCE`, passed at `sim/engine/prices.py` in `solved_prices`), so editing code outside that closure keeps the cache. The digest costs a few hundredths of a second per process once the closure list is cached (profile script: time `environment_digest` twice in one process).
- A cold price solve whenever a year completes a technology set or wage band the cache has not seen is the expected cost of caching, not a defect. Measured on the committed catalogue with an empty cache (Rome, no technologies, profile of `prices.solved_prices`): a few seconds cold under the profiler, about 64 fixed-point iterations, most of it demand clearing in `sim/world/need_demand.py`; the same call warm from disk is milliseconds. No cheap change was found: the iterations are the solver's convergence, and cutting them or the demand clearing belongs to the solver work in 321 and `docs/architecture/`, not here.
- `_dashboard_history` growth: done, a per-game cap option, off by default (test `dashboard_history_cap`).
- No-op commands: done. `save_state` skips the write when the text and the file are unchanged (`sim/engine/saveload.py`, `_ON_DISK`); this covers `open <id>` on something already running, which is refused before anything changes (test `complaint_181_save_cost`). What an `open` still pays is reading the save, because every `--session` command is its own process; a session is only cheaper than that if the process stays alive, which the plain `play` loop already does.
- README and `.cache/`: done, the Saving section now says what the folder is and that it is safe to delete.
- Final-playtest save requests (test `session_save_companions`): export/import instructions are in the README Saving section; a session save now keeps rotating year-start checkpoint copies in `FILE.backups/` (count is the declared `CHECKPOINTS_KEPT`), a plain-text `FILE.summary.txt`, and records the writing build in the save as `_game_version` for display only (nothing checks it on load, per CLAUDE.md 4.6); a session or save name ending `.json.gz` is written compressed and every reader (load, the civilisation and goal peeks, the save browser) reads either form. Save-browser metadata is 246.

Measured with every command as its own `--session` process on a 4-core container:
- Early/mid game: every command ~0.45-0.55s, almost all load+save. Slow steps (1.9-3.4s) only in years completing a never-seen set of technologies; cause: price solve cached in `.cache/price_solves/` (moving that folder aside reproduced 2.05s; the warm rerun took 0.58s).
- Late game (550-600 AD, ~500-960 concerns, ~240 projects): `step 1` 3-52s per year. Same save stepped twice on copies: 7.14s then 4.08s, so ~3s is the solver and ~3s the year itself; a bare `state` took 0.95s with a 2.0 MB save (374 KB at 256 AD).
- `open <id>` costs ~0.29s even when it only answers "already running" (20 in one process: 6.74s); 1,008 opens took 265s.
- The game writes `.cache/` into the folder it runs from; the README does not mention it.

What it would take: profile the late-game step; make refusals that need no simulation cheap; cap or compress the log in the save.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 210, 221, 222; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): a single late-game `step` took 8 to 20 seconds at 1,000 to 1,860 employees and 250 to 375 concerns, growing with size; the tester wants a visible progress indicator even for single years (see 221 for the multi-year case, which also loses all years on interrupt).

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): final save about 917 KB in a hosted container where temporary storage can vanish; asks for clear export/import instructions, automatic rotating checkpoint backups, reliable save-browser metadata (filed as 246), save-version information, optional compression and a short human-readable summary beside the machine-readable save. The compact writer already exists; the rest is open. Reproduces: untested.

**Also:** a multi-year `step N` with a `--session` file now saves after every simulated year (`sim/ui/proto/step_progress.py`), so an interrupt keeps the finished years. Each save costs what one late-game save costs, so a long step pays it once a year; measure before and after with a late save if saves are slowed further.

Update (Complaint 331): see `321` for the measured per-year CPU at years 100 and 150 after firms began to grow instead of multiplying.

Related: 304.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 141 (`closed/141-yearly-cost-grows-with-built-nodes.md`): yearly cost grows with built nodes.
- 321 (`closed/321-late-rome-year-still-costs-copying-and-clearing-work-per-actor.md`): late Rome year still pays final demand per trial price, a price solve per gate set and a revenue recompute; see Complaints/reports/caching-and-algorithms-review.md (owner: fix algorithms, not caches).
- 390 (`closed/390-the-agent-economy-is-slow.md`): the agent economy is slow (owner: wire first, optimise after).
