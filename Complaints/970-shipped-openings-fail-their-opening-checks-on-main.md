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

## Movement between the rebuilds d846ed11 and e927bb6c (England `spin_up_settled`, Norse ores and coin metal)

Read with `python3 sim/simulator.py opening-checks --civs england_1300,norse_900ad --json`, the saved `spin_up_result` of each shipped opening
(`openings/agent_economy/*.json.xz`, key `spin_up_result`, its `gaps` by quantity) and one-off probes that step the economy
(`blank_economy` then `economy.step`) in checkouts pinned to d846ed11, 8367df30, 526dd597 and the branch head.

### England: not a regression of 978, 613 or the solver change

- `spin_up_result["gaps"]` names the quantity: `unmet_need` (the food floor units short), in both rebuilds. The old rebuild's `unmet_need` gap
  was already the largest one; the new one is the same quantity in a different draw.
- `unmet_need` is not a settling quantity in England's economy: a continental tile (`germany_02`, `france_05`, `france_03`,
  `united_kingdom_03`) is short of food in some years and fed in the next, in every pinned checkout, including d846ed11 and 8367df30 (before
  978 and the solver change), with the same year-0 shortfall on `france_05`. A year with no shortfall beside a year with one reads as a change of
  the whole shortfall over a floor of one food unit (`SPIN_UP_UNMET_FLOOR`, `sim/markets/spin_up_gap.py`), so the gap is the shortfall itself,
  and which draw the last measured years land on decides whether it reads small or enormous.
- Turning the 613 carrier funding off (`carriage_funding.fund_bids` replaced by the identity) leaves the shortfalls unchanged, and the merchant's
  bids are funded in full each year. England's trajectory on 8367df30 and on the head agree year by year (same shortfalls to the last digit).
- Open (not caused by these changes, not fixed here): why those tiles' food is short in alternate years, and whether `SPIN_UP_UNMET_FLOOR`
  (an absolute one food unit against shortfalls of the size of a tile's population) is a floor that can close. Changing the floor loosens
  a measure, so it was not touched.

### Norse: Complaint 978 (borders across straits), through a bug in the opening placement

- Cause commit: a853d1e3 (978). The tree at 526dd597 (978 without the solver change) reproduces the head's Norse figures exactly
  (`silver_kg` price and making cost, stale ores, `prices` gap); 8367df30 (just before) does not.
- What changed for Norse: `norway_04`, `norway_05` and `norway_06` (Svalbard; the civilisation's `home_tiles` hold them with an opening
  population) lost their only land links, so no route reaches them from the rest (`CarriageTable.costs_from(port_tile)` omits them). Every other
  carriage cost from the port is identical before and after.
- Effect: each market area of a good now has a separate area of just those three tiles. `location_inputs.place_oriented` averaged a processor's
  output carriage over all its output areas, so one unreachable area made the output carriage of every tile infinite and no tile was costed
  finite: the processors of fixed-site inputs (`iron_bloom_kg`, `copper_kg`, `brick_1000`, `ceramic_kg`, `wood_tar_kg`, `glass_raw_kg`, `soap_kg`,
  `tallow_kg`, `wood_ash_kg`, `wooden_tools_kg`) were placed nowhere. The opening then makes far fewer goods in its first year
  (the output goods of `economy.step` in year 0), no ore or silver market trades, `iron_ore_kg` and `copper_ore_kg` read stale (so
  `price_over_cost_sited_ores` had no ratio and reads n/a; `detail["unmeasured"]` is empty for that group because the check names only
  the staple and the coin metal), and `silver_kg` trades at a price far over its making cost (`price_over_cost_coin_metal`).
- Confirmed by restoring one link (`norway_05` to `sweden_04`) in a pinned copy of the 978 tree: the markets that trade in year 1 and the
  producers return to the pre-978 set.
- Fix: `location_inputs.output_haul_cost` averages over the areas a tile can reach and is infinite only when it reaches none;
  `place_oriented` uses it. Regression test: `sim/tests/test_location_inputs.py` `OutputHaulCostTests`.
- After the fix, a Norse economy stepped one year trades the same number of markets as on d846ed11 (a probe printing the count of markets
  with `memory.traded_within(key, RECENT_TRADE_YEARS)`), instead of fewer than half.
- Left open: `mean_haul_cost` (inputs) has the same shape when a supplying tile is unreachable from the candidate, and the Norse
  `home_tiles` include populated Svalbard tiles that now have no route at all (not even by sea in the carriage table). Whether the sea links
  in `data/world/geography/sea_links/links.json` should reach them is a question for 978; a cut-off island should trade by sea if its people hold
  the means, rather than drop out of the economy.
- The shipped openings must be rebuilt after this fix (`python3 sim/simulator.py openings --prune`); the Norse and England figures above
  are those of the stale rebuild.
