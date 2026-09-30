# Performance

Measured on this container (4 cores), with every command run as its own process through `--session` (load the save, run one command, write the save). Timing log: one row per invocation, wall-clock seconds.

## Per command (from 257 AD on, 492 invocations)
| Command | Runs | Median | Max |
|---|---|---|---|
| step 1 | 79 | 0.53s | 2.20s (see Slow steps below) |
| why | 96 | 0.47s | 0.65s |
| start | 46 | 0.47s | 0.63s |
| path | 186 | 0.46s | 0.63s |
| state | 25 | 0.49s | 0.58s |
| ventures | 62 | 0.46s | 0.54s |
| open | 14 | 0.45s | 0.53s |

Spot checks (median of 3, fresh copy of the save each time):
| Save | Save size | Load+save only | state | step 1 | step 5 |
|---|---|---|---|---|---|
| 118 AD | 70 KB | 0.38s | 0.49s | 0.47s | - |
| 129 AD | 107 KB | 0.40s | 0.51s | 0.54s | - |
| 256 AD | 374 KB | 0.45s | 0.56s | 0.54s | 0.65s |
Across the 256 AD commands the slowest was `stuck`, at 0.62s.

## Slow steps (over 1s): the price solver on a new set of technologies
Steps over 1s: 320 (1.94s), 332 (2.20s), 353 (2.14s), 367 (3.38s), 369 (1.93s), 370 (2.29s), 375 (2.17s), 386 (2.39s). Every other year: 0.47-0.75s.
- Every slow year had projects completing, and pure `step 1` years on a copy (no starts, even with 27 closures, a fire and new historical events) never exceeded 0.75s.
- Not every completion is slow, and a slow step is not repeatable. The same "3 completions" step at 387 AD took 2.14s the first time and 0.58s on every replay.
- Cause, confirmed: the game caches price solves in `.cache/price_solves/` inside the game folder (37 files, 480 KB at 387 AD, git-ignored). With that folder moved aside, the same step took 2.05s; run again with the cache now warm, 0.58s.
- So each first-time set of technologies costs one price solve, ~1.5s (up to ~2.8s), and repeats are free. It does not get worse as the game gets longer, but it lands in exactly the years a player is most active.
- Side note for players: the game writes that cache into the folder it runs from, which the README does not mention.

## What this means
- Almost all of the cost of any command is the ~0.4-0.45s to load and write the save. A year of simulation adds only ~0.1s, and 5 years add ~0.2s.
- The save file grows over a game (70 KB -> 374 KB by 256 AD, most likely from the log, which had 1,049 entries by 303 AD). Load+save time grew only ~0.07s alongside it.
- There is no slow command at this scale. Whatever felt slow was my playing style: each routine year makes 5-18 separate invocations (ventures, one `open` per concern, `path` per goal, `why` per candidate, `start` per candidate, `step`), so a year costs 2.5-9s of wall time, almost all of it repeated load+save.
- Not measured: the peak of my run (~200-234 AD: ~40 concerns, ~120 staff, 17M den). The sackings shrank the game before I started timing, so a slower step at peak size is possible and untested.

## Suggestions
- A player running one command per process pays ~0.45s every time. Two things would help agents and scripts: a batch mode (several commands per invocation, which piping multiple lines already gives) and a smaller save (e.g. capping or compressing the log).

## Late game (552-559 AD): steps of 3-14 seconds
After switching to "research and open everything" (about 250 concerns running, 240 projects in hand, 30-80 new starts a year via `rush`):
- `step 1` wall times per year: 4.77, 4.76, 2.59, 9.02, 6.82, 11.10, 3.22, 14.12 seconds.
- The save grew to 2.0 MB (374 KB at 256 AD). A bare `state` now takes 0.95s, so load+save alone doubled.
- Same save stepped twice on separate copies (559 AD): first 7.14s, second 4.08s. So ~3s of a slow year is the price solver meeting a new set of technologies (cached on the second run), and ~3s is the year's simulation itself at this size.
- So the late-game slowdown is partly real growth, which the price cache cannot absorb. The years with the most completions (30-40 a year here) are the slowest.

## `open` costs ~0.3s even when it only refuses
At 585 AD (702 concerns running), one invocation carrying 1,008 `open <id>` lines took 265s. 892 of those were answered "already running". Timed on a copy: 1 x `open ag2_roller` (already running) 1.22s including load+save; 20 x the same 6.74s, i.e. ~0.29s per refusal. A player never sends 1,000 opens by hand, but a refusal that needs no simulation should be near-instant. The slowness here was mostly my own approach, forced by `ventures` not listing shut concerns (quirks #21): the complete fix on my side was to diff the complete *running* list from `ventures json` against everything ever built.
