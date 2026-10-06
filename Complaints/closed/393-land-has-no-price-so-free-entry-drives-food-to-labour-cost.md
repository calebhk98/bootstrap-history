# Land has no price, so letting makers grow wherever a price beats cost drives food to bare labour cost

**Status:** closed - folded into 398

On the agent economy, farmland is not scarce to a producer: a land-using recipe pays no rent and tiles have far more arable hectares than producers use. Two attempts to let production follow price (new makers wherever a known recipe's break-even price is below the market price, and producers with no plant growing while their runs pay) both drove grain toward the cost of its labour alone, which made an hour of unskilled work buy several times the grain the current model gives, and made grain prices swing more. The current model avoids this only because makers enter just where buyers are turned away, so prices stay above cost.

Separately, thin local markets clear far above cost and stay there: on a tile where limestone has one tiny producer, a few buyers with high ceilings take what it makes at a price far above the cost of quarrying, nobody is turned away, so no maker enters, and a producer with no plant cannot grow (limestone and lime in Rome).

Evidence: `python3 sim/economy_validate.py --years 20 --seeds 1` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`) (wage_kg_wh, grain_vola) with either change applied; limestone prices by area in a Rome game (`record.memory.prices`, keys `limestone_kg|...`).

What it would take: land as a scarce factor with a rent (arable hectares per tile, worked by producers and households' own plots, rent to its owners), so food prices carry rent above labour cost; then let producers with no plant grow while their runs pay, and makers enter on price above cost.

Related: 387, 388.
