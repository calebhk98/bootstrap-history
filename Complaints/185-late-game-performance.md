# Late-game performance: slow steps, slow `open`, growing save

**Status:** partly - a command that changes nothing (refusals, a repeated `state`) no longer rewrites the save, saves are written compact through the C JSON encoder (a quarter smaller on the test fixture), and the per-year scans behind Complaint 145 are cheaper. Remaining: a price solve is still several seconds whenever a year completes technologies or moves wages the on-disk cache has not seen (`.cache/price_solves` is keyed on every sim source file, so any code change makes the first run cold), and the yearly `_dashboard_history` entries grow the save; capping them changes what `changes years:N` can answer, so it needs a decision.

Measured with every command as its own `--session` process on a 4-core container:
- Early/mid game: every command ~0.45-0.55s, almost all load+save. Slow steps (1.9-3.4s) only in years completing a never-seen set of technologies; cause: price solve cached in `.cache/price_solves/` (moving that folder aside reproduced 2.05s; the warm rerun took 0.58s).
- Late game (550-600 AD, ~500-960 concerns, ~240 projects): `step 1` 3-52s per year. Same save stepped twice on copies: 7.14s then 4.08s, so ~3s is the solver and ~3s the year itself; a bare `state` took 0.95s with a 2.0 MB save (374 KB at 256 AD).
- `open <id>` costs ~0.29s even when it only answers "already running" (20 in one process: 6.74s); 1,008 opens took 265s.
- The game writes `.cache/` into the folder it runs from; the README does not mention it.

What it would take: profile the late-game step; make refusals that need no simulation cheap; cap or compress the log in the save.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
