# A Rome opening has no charcoal producer, so smelters cannot run

**Status:** closed - fit_to_supply held only the timber's direct users; it now carries the hold down the chain and compares worked runs, so the opening makes the fuel its smelters burn

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

## Resolution

Two findings corrected the report. Charcoal does have producers at the opening: the chosen recipe is the tar kiln
(`wood_tar_kg`, charcoal is its co-product), so no `producer:charcoal_kg@` id exists until a later entrant is
sited; the probe's id prefix missed them. The real fault was in `opening_runs.fit_to_supply`:

1. It held the users of a good only deposits supply (wood now stands as timber, Complaint 539) to that supply, but
   stopped at the first stage. The kilns were cut to the timber while the smelters, silver works and bloomeries that
   burn their charcoal kept their full size, so the opening bid for fuel it had not made. `limited_goods` now follows
   the bound down the chain (a good is bound when every recipe making it is site-bound or uses a bound good), and
   every stage is held to the stage before it. No good is named.
2. It compared plant capacity (`capacity_runs`), which is larger than the runs worked by a different share for each
   recipe (`opening_income.working_share`), so even the first stage was mismatched. It compares runs worked
   (`expected_sales`).

Regression: `sim/tests/test_opening_inputs_have_suppliers.py` (on the Rome opening, every input is made in the
quantity the producers take; on a forest, kiln, smelter fixture, the kiln and the smelter are held in turn). Measure:
`python3 -m sim.tests --slow --only opening_inputs_have_suppliers`.

Not fixed here: charcoal made beside the timber is not always in the market area of the smelters beside the ore; it
crosses areas by trade and carriage. Complaints 511 and 558 (`economy_tin_dearer_than_copper`) still fail, with a
smaller gap than before this change.
