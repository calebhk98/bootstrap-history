# Land has no price, so letting makers grow wherever a price beats cost drives food to bare labour cost

**Status:** partly - land is now a priced factor (`sim/economy/land_market.py`: quality bands, differential and scarcity rent paid to the tile's cohorts, pinned by sim/tests/test_economy_land_market.py and test_economy_land_rent.py). The clearing rent no longer jumps where use spills into the next land band (quality now falls smoothly with use; pinned by test_economy_land_continuity.py). Remains: posted rent still follows the year-to-year swings of the producers' land asks and expected output price (producers and price solver, not the land market; measure with the fixture and `land_per_run`, see that test), entry on price above cost is still off, and the wheat recipe has no seed or draught input (data). See Complaints/reports/agent-economy-review.md

On the agent economy, farmland is not scarce to a producer: a land-using recipe pays no rent and tiles have far more arable hectares than producers use. Two attempts to let production follow price (new makers wherever a known recipe's break-even price is below the market price, and producers with no plant growing while their runs pay) both drove grain toward the cost of its labour alone, which made an hour of unskilled work buy several times the grain the current model gives, and made grain prices swing more. The current model avoids this only because makers enter just where buyers are turned away, so prices stay above cost.

Separately, thin local markets clear far above cost and stay there: on a tile where limestone has one tiny producer, a few buyers with high ceilings take what it makes at a price far above the cost of quarrying, nobody is turned away, so no maker enters, and a producer with no plant cannot grow (limestone and lime in Rome).

Evidence: `python3 sim/economy_validate.py --years 20 --seeds 1` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`) (wage_kg_wh, grain_vola) with either change applied; limestone prices by area in a Rome game (`record.memory.prices`, keys `limestone_kg|...`).

What it would take: land as a scarce factor with a rent (arable hectares per tile, worked by producers and households' own plots, rent to its owners), so food prices carry rent above labour cost; then let producers with no plant grow while their runs pay, and makers enter on price above cost.

Related: 387, 388.
