# An iron mine sunk for a few denarii sells millions of iron

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, Rome, seed 11, around 109 AD). `buy mine iron 100` cost a few denarii to sink and
tens a year to stand; the founder's iron then sold at thousands of denarii a tonne, so a few thousand tonnes raised
millions. The player made and sold something, so it is not an exploit by the rules, but the margin is not plausible.

Likely cause: iron opens far above its making cost on this branch (558 lists `sited_ore_price_over_cost` red;
519's last section has the fix, opening producers with a working stock instead of a year of inputs, held back until
the spin-up settles, 473). Measure the founder's mine cost per tonne against the shown iron price at the opening.

What it would take: iron near its cost at the opening (519, 473), and a test that a founder's mine output sells at
a bounded multiple of its cost per tonne.
