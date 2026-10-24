# Tin shows far below copper in the opening year; the cause is copper's scarcity price, not tin's recipe

**Status:** partly - recipe mass balance fixed; the opening-year tin-over-copper reading (the deleted slow check `economy_tin_dearer_than_copper`) stays red until the opening settles (473) and the price stage of 507 lands; tracked on GitHub as #65

**What is wrong now.** Opening-year shown tin over copper is far below the ratio of the labour their recipes embody
(history: 0.015 before the mass-balance fix, about 0.1 on the latest decomposition against 0.441 required).
Measure: `python3 sim/simulator.py play --civ rome_100ad --seed real25`, `market` screen (shown tin over shown copper, against
the ratio of the labour their recipes embody through every input). The slow check that did this is deleted: it read the
opening year after one economy step and could not name a function.

**What is not the cause** (measured, `Complaints/reports/511-history.md`):

- Tin is not below its labour or its cost: gravel sellers, tin works, site limits, carriage and area choice are all fine.
- Cash, loans, ore and plant capacity do not bind copper in year zero.
- The skilled-labour (smith) ceiling does not hold copper down: it caps the quoted wage, not the hours
  (`sim/tests/test_labour_core_skilled_ceiling.py`); no source shows a craft premium rising above its long-run level when
  the craft was short (`Complaints/reports/research-how-trades-spread-and-skill-premia.md`).

**Cause.** Copper clears at several times its making cost while tin clears near cost. The smelters' `last_runs` are the
opening's seed (idle the year before) and each may move only `OUTPUT_CHANGE_SHARE_PER_YEAR` of capacity a year, so supply
cannot follow the demand of bronze; achieved runs then fall below plan on unskilled hours, furnaceman hours and flux.
Copper's inputs (charcoal, ore, wood) carry scarcity that tin's barely do. This is the unsettled opening (473,
`spin_up_result["settled"]` is false) plus input makers that never grow from a starved market (flux: `entry_sizing.sized_runs`
caps a newcomer at `ENTRY_SHARE_OF_TRADED_VOLUME`).

**What it would take.** A settled opening (473); a rule that tells a starved market from a phantom gap so input makers can
grow (sizing on traded volume plus buyers turned away fixed flux but contradicts
`test_a_gap_far_beyond_the_trade_is_sized_to_the_trade`, so it was not kept); then the check turns green with no tin
special case (CLAUDE.md 4.7).

**Fixed so far.** `cassiterite_kg` is the gravel dug and washed and `tin_kg` asks for the gravel its deposits' grade implies
(`data/production/20_nonferrous.json`); lead and mercury were restated the same way
(`sim/tests/test_ore_recipe_mass_balance.py`).

**Tried and why it failed.** Tripling `EXPANSION_SHARE_PER_YEAR` left copper unchanged (plans stay bounded by last year's
runs and inputs); removing the 25 percent pace left year-zero copper unchanged (hands were all hired); sizing entry from
unfilled bids (559) did not move flux or copper in the short Rome run; a longer spin-up made copper worse (the ask raise on
sold-out sellers keeps ratcheting).
