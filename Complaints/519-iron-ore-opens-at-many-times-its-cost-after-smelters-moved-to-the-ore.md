# Sited ores open at many times their making cost

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

Checked in 520: sizing the unsized districts (and drawing deposits down by their rate) leaves Rome's iron sites
as they were (all six already sized); Rome's iron ore price over its making cost falls somewhat but stays far above
1, so it is not a deposit-size problem on the Roman rows. For the other civilisations the new sites move some ore
ratios up and some down (measure with `economy.agent_prices()` against `_material_prices()` after a first step).

## Widened (2026-10-15)

The pattern is general: in 520, Han's copper, tin, lead and gold ores sat near their making cost while they had no
site and rose to several times to tens of times it once their districts named sites; Mexica copper and gold rose
the same way. So a site's yearly room (a share of the deposit's endowment per year) may be far tighter than what a
district can actually raise, and the scarcity shows as price. Check the site-room rule (`resources_working_share_per_year`,
how a site's room per year is derived from its endowment) against the historical output rates the deposit data
gives (`sim/engine/deposit_history.py`), for every civilisation, before changing the opening.
