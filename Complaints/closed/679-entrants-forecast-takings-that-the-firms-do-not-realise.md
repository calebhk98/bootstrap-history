# Entrants forecast takings that the firms do not realise

**Status:** closed - an entrant's forecast and a firm's books now charge the same things. The levy on takings is in the entry forecast (`firm_entry.expected_levy`); a firm weighs the site rent and manager's hours a step adds before it expands (`firm_expansion._added_carry`); a firm whose only concern is the technique runs it whole, with no pilot trial (`adoption.displaces_nothing`). Rule tests: `entry_forecast_matches_exit`, `firm_expansion`. Whole game: `python3 -m sim.tests --slow --only firm_count_whole_game_scenario --jobs 1` (the count per year is printed by a scratch probe over `firms_after`; the largest market now settles near where entry stopped).

In `firm_count_whole_game_scenario` (largest market), the firm count runs 23, 27, 27, 27, 27 and then falls to 8 by year 20,
where it stays. Entrants in one year count each other (`sim/agents/entry_round.py` `NicheEntry.found` passes `waiting + 1`
to `firm_entry.expected_entry_gross`), and a firm leaves only once its ramp ends and its margin is below the market's return
on its plant (`sim/agents/firm_exit.py`). So with 27 firms in, the realised margin falls short of what the entry forecast
(`AgentsPort.entry_gross` with those entrants, then the entry costs in `NicheEntry`) promised. One of the two sides
mis-states the takings or the costs of a firm among many.

Measure first: for the largest market, print per year each firm's forecast at entry (`last_margin` when founded) beside its
realised margin after the ramp, and the cost lines on each side (entry: `costs`, `stake_cost`; exit: plant times market rate,
interest). Then fix whichever side is wrong, with a rule test that builds both sides from the same inputs and asserts that a
firm admitted by entry is not one exit would close at full ramp in an unchanged market.

Command: `python3 -m sim.tests --slow --only firm_count_whole_game_scenario --jobs 1`.

## What was found (measured)

Measured with a scratch probe that logged, per firm and year, the forecast at entry (gross, costs, plan) beside the realised
margin, the plant's size, its adoption weight and the pieces `business_books.operate` and `carry` book.

- The entry side was sound for a firm of one founding size: its gross is the category's share with the entrants counted, its
  costs are upkeep, wages, rent and a manager's hours, and its capital hurdle (`stake_cost`) is of the same order as exit's
  (`plant` times the market rate, both priced by `imitation.copy_plan`).
- Cause 1, an entrant's plant did not run at the size it forecast. A firm that copies a concern knows a technique outside the
  baseline, so `adoption.advance_actor` started a pilot trial on it; `business_books.operate` (plants run at the adoption share)
  then ran its only plant at the pilot share for years, while `business_books.carry` charged rent and management on the whole
  size. Realised margin was the carry, a loss, and firms closed after the loss run. A trial displaces an incumbent technique;
  a firm that runs nothing else has none. It now runs the technique whole.
- Cause 2, firms grew past what the market holds. `expansion_gain` weighs takings less upkeep and wages but not the rent and
  management a step adds, which `carry` charges and entry weighs. The first plants, facing a market the waiting entrants had
  not yet reached, saw a large margin and added capacity until the market held a multiple of the sellers entry had counted; the
  shake-out followed. A step is now weighed after the carry it adds.
- Cause 3, smaller: the entry forecast ignored the state's levy on takings, which the books pay and exit's margin is net of.
  It now deducts `government().assess` of a probe firm. The scenario's levy is zero, so it does not move the scenario.

Neither entry nor exit was wrong in its own rule; the books and the expansion rule disagreed with both.

## What was done

Rule tests build entry and exit from the same market: a niche is run by the firms entry admits, and none is below exit's hurdle,
with and without a levy; a firm with only the technique has no trial and a firm with a second concern still trials; an
expansion step whose carry outruns its margin is not built. Counts per year of the largest market before and after:
see the commit message.

Left open, same area: a probe firm has no staff yet, so its visible scale (and so its levy share) is the lowest the state
assesses; a fresh firm's levy is under-forecast where the levy grows with a firm's size.
