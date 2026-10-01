# The founder's capital grows tens of times in the late game, and nothing compares it with the economy it lives in

**Status:** open

In a Rome seed-1 run with the recommended strategy the founder's capital rises steeply between years 100 and 150 (measured by the firm-entry and capital-market checks; Han does the same on some seeds). By year 100 the founder holds a few percent of one year's society output at most; nobody has measured the share at year 150. Some seeds stay near zero and others take off between years 75 and 100, so the outcome is bimodal.

Why it matters: a founder who ends up owning more than the economy can produce, or whose wealth compounds with no market, tax or political limit, makes every late-game strategy look the same. Historically the richest private fortunes were a few percent of the economy's yearly output; that is a validation range, not a target.

What to measure first: founder capital against `society_output()` (sim/engine/actors/world.py) every decade to year 150, for Rome and Han, seeds 1-4, and what the founder's income is made of when it takes off (concern revenue, interest, rent, sales to the state). Then decide whether the cause is a mechanism that is missing (saturation of the founder's markets, taxation of visible wealth, interest groups pushing back) or one that is wrong (revenue still authored, `Complaints/287`, `462`). Related: `535`, `550`, `412`, `114`.
