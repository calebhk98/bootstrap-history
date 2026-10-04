# Silver is too cheap to produce

**Status:** partly - ore dressing, roasting, cupel bellows and hearth attendance are now costed and the silver recoveries applied; silver is still far cheaper than the attested day wage implies, see 305

Money is anchored to each civilisation's coin metal at its solved production
cost. For Rome the solved cost of silver makes the opening labourer wage about
three times the commonly attested first-century day wage of about one
denarius. The model is not tuned to history (CLAUDE.md 4.1), but the record
should be a plausible outcome (4.2), and a threefold miss points at the
production side: silver's extraction and smelting labour (ore grade, recovery,
cupellation losses, mining labour per tonne at the deposit depths) is likely
too low.

Measure with the solved silver price in labour-hours
(`python3 sim/engine/solve_prices.py`) and the opening wage (`help` / `state` in a
Rome game), and compare to the attested day wage.

## What it would take

Re-derive the silver chain in `data/production/` from physical sources
(Laurion and Rio Tinto ore grades, cupellation yields, shaft labour at depth
from `sim/world/deposits.py`), then re-measure the wage. Do not adjust any
number to hit the day wage.

## Progress

- [x] Measured (`python3 sim/engine/solve_prices.py --civ rome_100ad --why silver_kg`,
  the figure the engine anchors money to): Rome's solved silver cost fell
  from about 1112 to about 1381 labour hours per kg after the fix below, so
  one denarius went from 3.00 to 3.73 labour hours (the coin is 2.7 g).
  England and Norse (also silver-coined) move by a few percent; Han (bronze)
  and Mexica (cotton) do not move.
- [x] The lead recipe reduced the ore once but the cupellation litharge is
  reduced back to lead a second time; fuel and furnace hours now count both
  passes (labelled heuristic: second pass equal to the first).
- [x] The direct silver-ore recipe used a 5 kg/t grade and 25 h/t of mining;
  the silver deposits give about 0.8 kg/t and about 54 h/t of rock. Both now
  follow the deposits, and `sim/tests/test_silver_chain_physics.py` pins the
  agreement.
- [x] Curated per-tonne mining running costs are gone; mining opex is the
  deposits' extraction labour at the miner wage (see 140).

## Remains

- Silver is still roughly three times cheaper in labour hours than the
  attested day-wage ratio implies. Measured causes, none of them tuned away:
  the batch is split between lead and silver by demand-anchored value, so
  silver bears most of the batch whatever the physical effort (the market
  and demand agent's area); ore dressing (crushing, washing, concentrating)
  is not costed apart from the rock-breaking figure; drainage and ventilation
  of deep workings are folded into one haulage multiplier.
- The recipe's 0.46 kg of silver per tonne of lead is far leaner than both
  the deposits (`britannia_lead` carries about 3.3 kg per tonne of lead) and
  the empire totals in `data/world/resources.json` (silver output over lead
  output is several times larger). Making it consistent would make silver
  cheaper still, so it was left, and needs the deposit byproduct data
  reconciled first.

**Also:** the lead recipe's silver yield per tonne of lead is far leaner than the deposit data implies, and was left inconsistent because matching it would make silver cheaper still. That is choosing data by the price it produces (CLAUDE.md 4.1). Make the recipe agree with the deposits whichever way the price moves; if silver then comes out even cheaper, the remaining gap is in what is not yet costed (ore dressing, the joint-cost split), and that is where to look.

## Progress: the lead recipe agrees with the deposits (fourth increment)

- [x] The lead recipe yields about 3.33 kg of silver per tonne of lead (it was 0.46), which is what `data/world/deposits.json` carries (the argentiferous deposit's 0.5 kg per tonne of rock over 150 kg of lead per tonne of rock) and is the right order against the empire totals in `data/world/resources.json`. `sim/tests/test_silver_chain_physics.py` pins the agreement.
- Solved silver, labour hours per kg (`python3 sim/engine/solve_prices.py --civ <civ> --why silver_kg`; here read through `engine.prices.solved_prices`): Rome 1449 before, 237 after; Han 1456 before, 235 after; England 413 before, 157 after; Norse 202 before, 112 after. Lead per kg also falls (Rome 0.150 to 0.025 hours). Mexica has no silver price.
- Money is anchored to the coin metal, so for Rome one denarius is now worth about a sixth of what it was in labour hours and the opening wage is correspondingly higher in coin terms than the attested day wage. The first-order reason is the joint-cost split (silver bears most of a batch whatever its physical effort) together with uncosted ore dressing; those are where to look, see 291. Tests that fixed absolute coin amounts now state them in labour hours (`test_affordability_and_credit`, `test_complaint_173_credit_forecast_once`).

## Progress: dressing, roasting and cupellation costed (fifth increment)

- [x] `lead_kg` gains labourer hours for dressing the rock to concentrate (about 8.5 tonnes of rock per tonne of lead from the deposits' grades), roasting and cupellation bellows air (from 2 Pb + O2 -> 2 PbO and a blast excess), and furnaceman hours for the attended cupel; `copper_kg` gains dressing and roasting. The rates are labelled conf D in each `yield_basis`; the tests pin floors (`sim/tests/test_silver_chain_physics.py`).
- [x] The 0.90 and 0.92 silver recoveries stated in the recipe's text are now applied (see 291).
- Solved silver, labour hours per kg (`python3 sim/engine/solve_prices.py --civ <civ> --why silver_kg`): Rome 224 before, 319 after; Han 233 to 333; England 156 to 205; Norse 112 to 135. One Rome denarius went from about 0.61 to about 0.86 labour hours.
- Rome silver breakdown per kg after (319): charcoal about 56, galena (mining, from deposit cost) about 113, furnaceman about 74, dressing, roasting and bellows about 68, smith about 8, capital under 1.
- Drainage and ventilation are not a missing step: they are inside `HAULAGE_MULTIPLIER_DEEP_VEIN`, underived. Left as is, filed in 305.
- Rome's opening wage is still about twelve denarii for a ten-hour day against the attested one. The physics at the deposits' grades does not close the gap; 305 lists where it may lie (grade, drainage, mine ownership and the state's take) without tuning.

## Update (silver-and-gold-cost)

Ore grade rechecked against Laurion and Rio Tinto assays and kept; see 305 and 333 for what remains.

## Update (mine-labour-per-tonne)

Labour per tonne of rock checked against Kongsberg and Melle figures and fire-setting wood added to hard rock; silver moved from about 319 to about 335 hours per kg and the gap remains. See 342, 343, 344.

Related: 284, 349.
