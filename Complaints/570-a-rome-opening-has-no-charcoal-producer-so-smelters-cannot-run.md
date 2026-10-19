# A Rome opening has no charcoal producer, so smelters cannot run

**Status:** open

Found tracing 559 and 558. At a Rome opening (`ROME_SPIN_UP_YEARS=2,1`, game built as `play` builds it) the agent
economy holds no `charcoal_kg` producer with any capacity, on `origin/main` as on this branch, while firewood and wood
have producers on most held tiles. Copper smelters plan runs and bid for charcoal, hold ore and flux, and run nothing
until the copper price climbs; Algeria's smelter is the traced case (Complaint 559, last section).

Measure: build the game (`simulator.Sim(..., civ=simulator.load_civ("rome_100ad"))`), then count
`record.producers` whose id starts with `producer:charcoal_kg@` and their `capacity_runs`; compare `firewood_kg`.

Why it matters: charcoal is the fuel of every ancient smelter, so copper, bronze, iron and silver all start short.
This is the likely root of `economy_tin_dearer_than_copper` and `economy_bronze_market_price` (558) and of copper's
scarcity price (511), and it moves every metal price a player sees.

What it would take: find why the opening sizes no charcoal producer (the opening sizes producers from final demand,
and charcoal is only an intermediate: check whether intermediate demand from smelters reaches the sizing, whether
the charcoal recipe's node is held, and whether its wood input is priced where it would sit), fix the cause for every
intermediate good, and test that each input a sized producer needs has a producer or a supply at the opening.
