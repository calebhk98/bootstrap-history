# The spin-up's settled test cannot pass near a zero rate, and tests the wrong state

**Status:** closed - the stop rule takes an absolute floor for the rate; the saved result describes the final trimmed state over consecutive years with output, employment, inventories and unmet need; the rebase keeps expectations (the cycle itself stays 473)

Found by an outside reviewer reading the repository; checked against the code.

- `_settle` (`sim/engine/economy_port_year.py`) measures the gap as `abs(new / old - 1.0)` over the price
  level, the interest rate and a few watched prices. A rate shrinking by a fixed share toward zero keeps
  that gap at the shrink share forever, so constant prices with a rate near zero report "not settled".
- The test runs before `trim_workforce_to_expected_hours` and `_settle_trimmed`'s further years; the
  saved `spin_up_result` describes a state the opening no longer has.
- `finish_spin_up` (`sim/economy/api.py`, `rebase_basket_price_level` in `year_close.py`) sets every
  expected inflation to zero. Its docstring says this is so the rebase is not read as a price jump, but
  when expectations were not zero it also changes saving and lending.
- Only prices and the rate are tested; output, inventories, employment and unmet needs are not.

## What it would take

- An absolute tolerance for quantities near zero (the rate) beside the relative one for prices.
- The settled test on the final state, after trimming, over several consecutive years, including real
  output, employment, inventories and unmet need.
- Rebasing that rescales expectations to the new base instead of zeroing them, or a measured reason
  why zeroing is harmless.
- Order of work, as the reviewer suggests: 546 and 547 first, then the opening (545, 526), then this
  measurement, then adjustment speeds (473).

Reproduced: `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60` matches the reviewer's
table year for year (the trace counts the first simulated year as year 0). The price level swings and
ends far below the opening, the unskilled wage falls to a small fraction of the seeded wage, and the
rate falls to a near-zero floor before jumping back. The run takes several minutes.


## What now happens

`AgentEconomy._settle` is the first stage's stop rule: it decides when that stage ends, so changing its
measure changes every opening. It and the reported result are now separate things.

- Stop rule (`_settle`): the price level and watched prices are measured by relative change, the rate by
  change over the larger of the rate and `SPIN_UP_RATE_FLOOR` (`sim/engine/spin_up_gap.py`, pure functions,
  tested without a game). A rate shrinking toward zero with constant prices now ends the stage.
- Reported result (`AgentEconomy.final_result`, saved as `spin_up_result`): measured after the workforce is
  trimmed, over the last `SPIN_UP_MEASURED_YEARS` consecutive years of the trimmed stage (those years were
  already run; no year was added). Keys: `settled`, `years` (all hidden years), `gap` (largest change; one
  when fewer than two years could be compared), `gaps` (by quantity), `measured_years`, `final` (the last
  year's state), `first_stage` (the stop rule's own result).
- Measured quantities: price level, rate, watched prices, real output (output at the opening prices),
  hours hired, producers' inventories (at the opening prices) and unmet need (`sim/economy/spin_up_state.py`).
- Rebase (`rebase_basket_price_level`): expected inflation is a yearly rate, the same in any base, so it is
  carried over instead of zeroed; only the last price level that households and the market compare against
  is reset to one. This changes saving and lending at every opening whose expectation was not zero.

Regression tests: `sim/tests/test_spin_up_measure.py`. Measure the new result on a full opening with
`python3 sim/simulator.py opening-checks` and `spin-up-trace --civ rome_100ad --years 60` (long runs).
