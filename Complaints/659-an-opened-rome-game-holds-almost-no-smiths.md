# An opened Rome game holds almost no smiths, so smith work is refused for want of people

**Status:** open

Found in deep extraction 3 (640). In an opened `rome_100ad` game the labour core's people of the smith trade read
about a thousandth of a person, against tens of thousands in an unopened game; `start horse_collar` is then refused
with cause `people_exist` ("no one left to do the smith work"). It reproduces on a clean checkout of the integration
branch, so it is not the extraction's doing. `start_and_upkeep_quotes_scenario` fails two checks on it.

Measure: `national_trade_population("smith")` (labour api) on `sim(civ="rome_100ad")` against `unopened_sim(civ="rome_100ad")`.

Why it matters: a trade the opening empties cannot be hired, so whole branches of the tree are refused at the start,
and 533 stage 2 now makes farms buy iron tools that smiths make.

What it would take: find which rule moves the opening's smiths out (the opening's placement by expected sales, the
post-spin-up trim to the plot trade, 551's landless cohorts, or 644's formation step), test it as a function, and fix
it so a trade the economy's recipes book hours to keeps the people that work them.
