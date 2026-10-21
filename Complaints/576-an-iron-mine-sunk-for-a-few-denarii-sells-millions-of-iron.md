# An iron mine sunk for a few denarii sells millions of iron

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, Rome, seed 11, around 109 AD). `buy mine iron 100` cost a few denarii to sink and
tens a year to stand; the founder's iron then sold at thousands of denarii a tonne, so a few thousand tonnes raised
millions. The player made and sold something, so it is not an exploit by the rules, but the margin is not plausible.

Likely cause (unverified, the status stays open while a measurement runs): iron opened far above its making cost on the branch of the playtest. 519 (now narrowed to precious ores; its common-ores check passes) records the cause as a year of inputs stocked at the opening and the fix of opening producers with a working stock instead, held back until the spin-up settles (473). Measure the founder's mine cost per tonne against the shown iron price at the opening, and check `sited_ore_price_over_cost` against the current red list in 558.

What it would take: iron near its cost at the opening (519, 473), and a test that a founder's mine output sells at
a bounded multiple of its cost per tonne.
