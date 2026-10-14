# Iron ore opens at many times its cost since smelters moved to the ore

**Status:** open

After merge 968974d4 (Complaint 473: weight-losing processors sit at their fixed-site inputs), a Rome opening's
iron ore trades far above its long-run cost (`economy.agent_prices()["iron_ore_kg"]` against
`market_price_ratio("iron_ore_kg")` after the opening; it was a small multiple before). Iron bar fell at the same
time. A blast furnace, which needs thousands of tonnes of ore to build, now costs more to open than a default
founder holds. Found fixing `closure_reasons` (the fixture now picks the cheapest concern to open).

Iron ore is common, so a scarcity price of that size is not plausible. The siting change keeps capacity that the
local ore supply cannot feed ("the shortage shows as the input's price") and concentrates smelters on a few ore
tiles whose site limits are small, so their bids for ore run far above its cost of raising.

What it would take: check the iron ore site limits against the deposits' data (they may be far too small, like the
ore mass balance fixed in 511), and size a processor's capacity at the opening to the input supply its tiles can
reach rather than keeping the excess as a price. Test: a common ore's opening price stays within a bounded multiple
of its making cost in every civilisation (a relationship, CLAUDE.md 4.2). Overlaps 507 Stage 2 (the opening);
check after it merges.
