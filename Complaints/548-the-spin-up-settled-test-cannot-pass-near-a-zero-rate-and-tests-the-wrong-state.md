# The spin-up's settled test cannot pass near a zero rate, and tests the wrong state

**Status:** open

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

