# Model results that tests were changed to accept

**Status:** closed - two checks restored to their original strength, one explained and given a stronger companion, one fixed in the model

While the full suite was brought back to green, a few checks were changed because the model no longer
produced what they claimed. Each was re-measured on the integration branch of the defect round.

- `test_population_farm_technique.py`: a food technology no longer raises Rome's population. **The original
  claim was wrong for Rome as the territory is set up, and right for a land-bound society.** The control and the
  improved game end the thirty years with the same population (run both with `_run_years` and compare
  `game.population.total`; they match to the person). Nutrition stays at need every year, so the fertility and
  mortality responses that read it never move. What binds is the demographic rates at need, not food: the farm
  workforce is sized by `LabourAllocationMixin._allocate_farm_workforce` to just feed the people, a surplus
  frees hands (`farm_workers_needed`), a shortfall calls for hands and then for clearing, and Rome's territory
  holds several times the farmland it has cleared (`_farm_arable_ceiling` against `farm_land.hectares`, printed
  by building `sim(civ="rome_100ad")`). Food can only bind once that ground is all cleared. The new check sets
  the ceiling to the cleared land and plays the same technique for `LAND_BOUND_YEARS`: the control's people turn
  down while the improved society keeps growing (`test_a_food_technology_raises_population_once_the_land_is_all_cleared`).
  The loosened check stays: with headroom the technology shows as fewer farm workers and no fewer people.
  Whether freed hands should also raise intake above need (income-driven eating, which the demography step
  reads only through the granary overflow) is a design question, not a defect of this check.
- `test_insolvency_whole_game.py`: a ruined founder's money turns round within three market years but is negative
  again around year five. **No longer true on this branch** (firm exit with creditor-first repayment). Measured
  over eight market years by setting `RUIN_YEARS = 8` and calling `_ruined_founder_run()`: the founder's money
  climbs every year from the ruin, crosses zero in the sixth year and keeps rising; debt over the credit limit
  falls every year. The original five-year check (`RUIN_YEARS = 5`, money at the end above money at the start)
  is restored.
- `test_economy_money_regimes_norse.py`: more mined metal raises the price level only weakly at four years.
  **No longer true on this branch.** `play("norse_900ad", 12, ...)` with and without `mined_share=0.1` (shared
  `money_regimes_play.py`): the stock is a multiple of the unmined twin, and the price level pulls clear of
  its twin from the fourth year on; the mean over the compared years clears the declared margin at a lag of four.
  The original lag (`MONEY_LAG_YEARS["norse_900ad"] = 4`) is restored. The baseline price level still cycles
  widely over the first decades (473), which is why the check compares a mean over several years.
- A fresh opened game throttles projects that use goods with no deposit and no producer capacity (alum, papyrus)
  to the floor, because their market tonnage is zero. **Fixed in the model.** Measured with
  `sim(civ="rome_100ad")`: of the materials the tree names, most have neither a deposit on the tiles held nor a
  producer plant; the starting installations' standing draw on alum alone holds the throttle at its floor from the
  first year, with the one line "the market is out of it". Each material now sits on a route
  (`MaterialReachMixin.material_supply_route`): held, market, imported, makeable (priced because a held
  technique makes it, but no producer runs it) or unavailable (no seller at all; work on it cannot start, see
  `material_availability.py`). A partner's tonnes now count in `_material_market_tonnes`, as the quote already
  counted them. The shortage says which case it is. The open part, that no producer enters for a good only
  projects ask for, is filed as 512.
