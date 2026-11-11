# A cold game build exceeds the hash-seed-order check's ten-minute limit

**Status:** closed - the check builds the cheapest base civilisation, which fits its limit, and passes

`hash_seed_order` (`sim/tests/test_hash_seed_order.py`, around line 82) builds a game in a subprocess with an empty spin-up
cache and gives it 600 seconds. On main before the Eurace port (5026213) the full slow suite passed it; on the branch
`section5-bugs-and-eurace-review` the subprocess times out even when the topic runs alone:

    python3 -m sim.tests --slow --only hash_seed_order --jobs 1 --topic-seconds 3000

The check itself (the same record under two hash seeds) never ran, so whether order still depends on hashing is unknown.

**Likely costs, none measured yet.** The opening now settles household own-plot growing and sold hours with the year's own
rules (`sim/economy/opening_own.py`), solves its interest rate (`opening_rate.py`), and places producers only where their runs
pay (`crop_sites.py`, `sim/markets/port_crop_prices.py`); the goods market clears by a logit over sellers
(`goods_market_logit.py`, which `unsold_search` calls once per bisection trial); merchants consider every paying
destination (`merchants._good_routes`). Complaint 497 owns the cost of a year; this is the cost of the opening and the
first spin-up years from a cold cache.

**What it would take.** Time a cold `harness.sim()` on main and on the branch with a profiler, name the steps that grew,
and cut them (or, if the time is inherent, say so here and give the check a limit derived from that measurement, never a
larger number picked to pass).

## Measured on branch claude/labor-market-economy-stability-ueffy1

The opening's land-rent covering (`opening._with_covering_prices`) adds, after the full solve, up to
`COVERING_PRICE_PASSES` reopens of two `_open` calls each (one sizes the mint's metal replacement at the covered prices,
`_reopen`). On the fixtures this multiplies `_open`, the income root-finds and households' `goods_orders` calls by two
to three; the per-call cost is unchanged. Counted with a scratch wrapper over `sim/economy/fixture_setups.py`'s
`stationary_setup()` and `small_setup(land_per_run=...)` (no committed command counts them). Cheaper options that move
the results slightly: size the replacement from the previous pass's record instead of a fresh open, or fewer passes.
Time Rome's opening with `ROME_SPIN_UP_YEARS=3,2 python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 1`.

## Closed

Measured on 32b9f3a7 with a fresh spin-up cache and `ROME_SPIN_UP_YEARS=6,0` (the check's script run alone under `time`): a cold Norse build took under two minutes and a cold Mexica build under three, while Rome's cold opening took well over an hour in the openings rebuild (the `shipped ... cache entries` lines of `python3 sim/simulator.py openings`). Rome's cost is its size (Complaint 497 owns the cost of a year and 473 the spin-up), so the check now builds `norse_900ad`: the same opening and year code. Its limit stays at ten minutes, several times the measured build. A timeout now kills both builds and fails the check instead of raising out of the topic. `python3 -m sim.tests --slow --only hash_seed_order --jobs 1` passes: the two hash seeds give the same record.
