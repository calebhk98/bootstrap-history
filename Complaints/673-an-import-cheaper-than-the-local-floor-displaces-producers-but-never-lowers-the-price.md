# An import cheaper than the local floor displaces producers but never lowers the price

**Status:** open

Found closing 672. A foreign cargo landed in a partner market displaces the partner's producers, who idle, but the price stays
at their floor: in `sim/world/market.py` the cargo is a price taker and nothing lets carriers compete by asking less than the
local producers. Before 672 the price fell, but only because idle capacity was carried as phantom stock and dumped. The two
checks in `sim/tests/test_foreign_actor_trade_scenario.py` that expected the fall were loosened to "never climbs above where it
began" and "no wider than it was" when 672 closed; they are this complaint's to restore.

**How it should work.** An importer offers at its landed cost (purchase price abroad plus carriage, dues and its margin). Where
that is below the local producers' floor, the cargo sells first and sets the price for the quantity it covers; local producers
cut runs and supply only what remains at their floor. Several carriers on a route compete down to their landed cost. This is the
agent economy's rule for merchants' asks; the world-market model should follow it or read it.

**What it would take.** The importer's offer enters `clear_market` at its landed cost, not as a price taker; a rule test on built
inputs shows a cargo cheaper than the floor lowers the price for its quantity and a dearer one does not; restore the two
scenario checks to their original claims with the bounds they had.
