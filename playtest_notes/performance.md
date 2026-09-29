# Performance

Measured on this container (4 cores), with every command run as its own process through `--session` (load the save, run one command, write the save). Timing log: one row per invocation, wall-clock seconds.

## Per command (from 257 AD on, 492 invocations)
| Command | Runs | Median | Max |
|---|---|---|---|
| step 1 | 79 | 0.53s | 2.20s (outliers: 1.94s in 320 AD, 2.20s in 332 AD; every other year 0.47-0.61s) |
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

## Outlier steps
Only two years out of 79 were slow: 320 AD (1.94s) and 332 AD (2.20s), 12 years apart. Both were ordinary years in my notes. I have not found what runs in those years. It could be a periodic recalculation (prices or demography) or chance; the per-year log `timings.csv` in my scratchpad is the evidence.

## What this means
- Almost all of the cost of any command is the ~0.4-0.45s to load and write the save. A year of simulation adds only ~0.1s, and 5 years add ~0.2s.
- The save file grows over a game (70 KB -> 374 KB by 256 AD, most likely from the log, which had 1,049 entries by 303 AD). Load+save time grew only ~0.07s alongside it.
- There is no slow command at this scale. Whatever felt slow was my playing style: each routine year makes 5-18 separate invocations (ventures, one `open` per concern, `path` per goal, `why` per candidate, `start` per candidate, `step`), so a year costs 2.5-9s of wall time, almost all of it repeated load+save.
- Not measured: the peak of my run (~200-234 AD: ~40 concerns, ~120 staff, 17M den). The sackings shrank the game before I started timing, so a slower step at peak size is possible and untested.

## Suggestions
- A player running one command per process pays ~0.45s every time. Two things would help agents and scripts: a batch mode (several commands per invocation, which piping multiple lines already gives) and a smaller save (e.g. capping or compressing the log).
