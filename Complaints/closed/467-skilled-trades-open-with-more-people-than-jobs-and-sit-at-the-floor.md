# Skilled trades open with more people than jobs and sit at the floor wage

**Status:** closed - after the hidden spin-up each non-fallback trade is cut to the hours producers plan to bid (or the market hired last year, if more); the freed people join the unskilled trade (`sim/economy/workforce_settle.py`, called from `finish_spin_up`). Regression: `sim/tests/test_complaint_467_trades_open_to_the_jobs.py`.

The agent economy's opening staffs hard trades from the able by the hours producers could work at
capacity (`sim/economy/labour_state.py` `opening_workforce`). After the hidden spin-up years producers
bid for far fewer hours than their capacity, so a skilled trade starts the game with several times more
people than jobs. A glutted trade pays the floor wage, so the smith earns what the labourer earns for
decades, until attrition thins the trade (entrants avoid a trade with no jobs). The mechanism for a
training premium is in the labour core and is tested (`economy_labour_core`); this is a starting-state
mismatch, not a missing mechanism.

Evidence: open the Rome game, then compare the labour core's people by trade
(`economy.record.workforce`) with the hours producers bid for in the first year
(`sim.economy.year_labour.sloped_bids` input). Smiths held several times the hours wanted.

What it would take: size the opening workforce by the hours producers will actually bid (their expected
runs, not capacity), or run the hidden spin-up until the workforce settles as well as prices. Producers'
own contraction during the spin-up (capacity falling to a fraction of the opening's) is its own question
in `sim/economy/producers*.py`.

Resolution: the opening workforce itself is still sized by capacity (it must exist for the spin-up); the trim
after the spin-up replaces capacity with expected hours, read from producers' own plans. Producers' contraction
during the spin-up stays a separate question in `sim/economy/producers*.py`.
