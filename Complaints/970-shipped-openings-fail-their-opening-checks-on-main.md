# The shipped openings fail their own opening checks on main

**Status:** open - found while rebuilding the shipped openings on branch year-speed-one-second; not investigated

`python3 sim/simulator.py openings` runs the opening checks (`sim/engine/opening_checks.py`) and refuses to ship an
opening that fails them. Every base civilisation fails at least one, so none can be shipped without `--allow-failing`.
`python3 sim/simulator.py opening-checks --civs rome_100ad,mexica_1500` on `main` (478dc816) gives exactly the values
the speed branch gives, so these are the game's state on `main`, not a branch's doing:

- every civilisation: `spin_up_settled` (the hidden spin-up does not settle; Complaint 473)
- `rome_100ad`: `money_against_wear` and `wage_over_floor`
- `mexica_1500`: `wage_over_floor`
- `han_china_100ad`: `money_against_wear` (just below its bound)
- `norse_900ad`: `price_over_cost_sited_ores` and `price_over_cost_coin_metal`
- `england_1300`: only `spin_up_settled`

After the speed branch's price-solve change (the solve stops at its own tolerance; the opening is a different draw of the
same rules), the set moved both ways: Rome no longer fails `money_against_wear`, Mexica no longer fails `wage_over_floor`,
Norse no longer fails `price_over_cost_coin_metal`, but Han now also fails `price_over_cost_sited_ores` (above its upper
bound). That the set moves with a change of last digits is itself evidence that the openings sit near the bounds and the
unsettled spin-up (Complaint 473) decides where.

A shipped opening is the opening a fresh environment computes for itself with the same code, so shipping one that fails
changes no game; refusing to ship only makes every fresh environment wait minutes for the same result. The checks therefore
belong to the opening, not to shipping.

Run `python3 sim/simulator.py opening-checks` for the current values and bounds (it takes minutes: each civilisation's
opening is opened). Why it matters: a check that every opening fails no longer tells a regression from the usual state, and
shipping needs `--allow-failing`, which also lets a real regression through. Either the openings should meet the bounds,
or a bound that does not describe a working opening should change, each with its reason.

## Measured on 2094a71f (rebuilding the five base openings)

`python3 sim/simulator.py openings --civs rome_100ad,mexica_1500,england_1300,han_china_100ad,norse_900ad --prune --allow-failing ...` printed the opening checks for each:

- every civilisation: `spin_up_settled` (473)
- `rome_100ad`, `england_1300`, `han_china_100ad`: `money_against_wear`, each a little under its bound
- `han_china_100ad`: `price_over_cost_coin_metal` reads n/a (the coin metal has no price at the opening)
- `mexica_1500` and `norse_900ad`: only `spin_up_settled`

## han_china_100ad `price_over_cost_coin_metal` n/a (read from code; the opened state was not inspected)

The check reads `bronze_kg` (Han's `coin_standard.material`, the economy's `backing_good`), not a coin-metal id of its own.
`price_ratios` in `sim/engine/opening_checks_run.py` left a named good out when any of four things held (no good, stale,
no price, no making cost) and printed n/a without saying which. Rome, England and Norse back their money with `silver_kg`,
Mexica with `cacao_kg`; Han is the only base civilisation whose money metal is an alloy made from two other goods (copper and
tin, recipe `bronze_kg` in `data/production/20_nonferrous.json`). The likeliest cause is that `bronze_kg` is stale at the opening:
the mint draws the opening metal from the book directly (`seed_opening_metal`, `sim/economy/mint.py`), nothing buys or sells
bronze on a market until copper and tin are both in reach, and the only tin site in the data near Han is `gejiu_tin`
(`data/world/geography/deposits/reference_output_sites.json`). That is a guess: a cold opening of Han takes longer than the
five minutes allowed here, so neither the shipped-opening load nor `opening-checks` could be run.
No price was invented. The check now records the cause per left-out good in `detail["unmeasured"]`
(`opening_checks.unmeasured_cause`: no_good, market_did_not_clear, no_price, no_making_cost), so the next
`opening-checks --civs han_china_100ad` run names it. If it reads `market_did_not_clear` or `no_making_cost` for `bronze_kg`,
the open question is whether Han's tin and copper reach the bronze recipe at the opening, not the check.

## Re-read on the rebuilt openings (commit d846ed11)

`python3 sim/simulator.py opening-checks --civs <civ>` for each base civilisation. Failing: every civilisation's `spin_up_settled` (473);
`rome_100ad` `money_against_wear` (just under its bound); `norse_900ad` `price_over_cost_staple` (millet far below its making cost);
`mexica_1500` `price_over_cost_sited_ores` (no value) and `wage_over_floor` (under one); `han_china_100ad` `price_over_cost_coin_metal`,
whose `detail["unmeasured"]` (`--json`) gives `bronze_kg: market_did_not_clear`: Han's coin metal does not trade at the opening, so it has no price.
