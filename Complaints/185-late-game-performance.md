# Late-game performance: slow steps, slow `open`, growing save

**Status:** partly - a late Rome step (about AD 250, seed 1) is several times cheaper: actors' per-trade staff is a kept running sum instead of a recount per read, concerns are counted by category in one walk, mining technology and market standing are kept per built/operating state, the stock ledger sweeps only after a new key, the actors' demand tally skips firms (result-identical on `perf_fingerprint.py check --quick`; what remains is filed as 471). Earlier: a command that changes nothing (refusals, a repeated `state`) no longer rewrites the save, saves are written compact through the C JSON encoder (a quarter smaller on the test fixture), and the per-year scans behind Complaint 145 are cheaper. A late save of a 150-year Rome run and a warm `available` measure well under a second each (profile script in the 145 history; a save is a fraction of a second CPU), so the remaining cost is the step. Remaining: a price solve is still several seconds whenever a year completes technologies or moves wages the on-disk cache has not seen (`.cache/price_solves` is keyed on every sim source file, so any code change makes the first run cold), and the yearly `_dashboard_history` entries grow the save; capping them changes what `changes years:N` can answer, so it needs a decision.

Measured with every command as its own `--session` process on a 4-core container:
- Early/mid game: every command ~0.45-0.55s, almost all load+save. Slow steps (1.9-3.4s) only in years completing a never-seen set of technologies; cause: price solve cached in `.cache/price_solves/` (moving that folder aside reproduced 2.05s; the warm rerun took 0.58s).
- Late game (550-600 AD, ~500-960 concerns, ~240 projects): `step 1` 3-52s per year. Same save stepped twice on copies: 7.14s then 4.08s, so ~3s is the solver and ~3s the year itself; a bare `state` took 0.95s with a 2.0 MB save (374 KB at 256 AD).
- `open <id>` costs ~0.29s even when it only answers "already running" (20 in one process: 6.74s); 1,008 opens took 265s.
- The game writes `.cache/` into the folder it runs from; the README does not mention it.

What it would take: profile the late-game step; make refusals that need no simulation cheap; cap or compress the log in the save.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 210, 221, 222; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): a single late-game `step` took 8 to 20 seconds at 1,000 to 1,860 employees and 250 to 375 concerns, growing with size; the tester wants a visible progress indicator even for single years (see 225 for the multi-year case, which also loses all years on interrupt).

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): final save about 917 KB in a hosted container where temporary storage can vanish; asks for clear export/import instructions, automatic rotating checkpoint backups, reliable save-browser metadata (filed as 250), save-version information, optional compression and a short human-readable summary beside the machine-readable save. The compact writer already exists; the rest is open. Reproduces: untested.

**Also:** a multi-year `step N` with a `--session` file now saves after every simulated year (`sim/engine/proto/step_progress.py`), so an interrupt keeps the finished years. Each save costs what one late-game save costs, so a long step pays it once a year; measure before and after with a late save if saves are slowed further.

Update (Complaint 550): see `471` for the measured per-year CPU at years 100 and 150 after firms began to grow instead of multiplying.
