# A scarce skilled trade's wage is capped today at its long-run training cost

**Status:** partly - this year's wage of a trade needing training now clears against bids (`sim/labour/market/scarcity.py`), the long-run cap stays on what entrants and switchers expect; the wheat path over the full 20 years and the slow checks are not yet re-run

`sim/labour/market/clearing.py` `clear_one` caps the year's wage of every trade at `trained_substitute_wage`: the unskilled
wage times the training premium. That is where the wage settles in the long run, once trainees have had time to qualify. A
trainee takes the trade's training years to arrive, though, so in the short run a trade whose employers bid far above the cap
should pay a scarcity wage (a quasi-rent) that draws its own workers' extra hours (`hours_share_at`) and switchers, and that
entrants weigh against the long-run cap.

Measured (473, Update 9): in Rome's opening, the furnacemen of `italy_02` are fully hired at a
wage of about 0.05 to 0.09 an hour while employers' bids carry a worth of 3.6 to 8.6. The trade's hired hours fall by more than
an order of magnitude over three years, the iron-bloom makers achieve a small share of their planned runs, and iron bar, iron
tools and then wheat run away in price.

**What the fix should do.** The long-run cap stays on what entrants expect to earn after training. Today's wage clears against
bids, bounded by the cost of bringing a trained worker in (`ImportCosts`, a real short-run substitute). Write the rule test
first: a thin trade with bids far above the cap and few workers pays above the cap this year, its workers offer more hours, and
an entrant's graduation income stays at the cap. Then re-run the 473 wheat probe.

## What was done

- `clear_one` bounds this year's wage by `scarcity.short_run_ceiling`: the long-run cost for a trade needing no training (hands move in at
  once) and for the unskilled trade; otherwise the hours-weighted worth of the bids (one stray bid with few hours does not set the wage, the
  434 concern), and no more than `ImportCosts` where trained hands can be fetched. No typed multiple.
- `Clearing.target_wage` (the heading wage entrants read through `income_at_graduation`) is capped at the long-run cost, so the cobweb guard of
  651 and 664 holds: an entrant's graduation income stays at the cap.
- Switchers: a destination is weighed by `income_at_graduation` (they train, so the long-run cap); a source by today's wage. A faster move
  within a skill family is only the shorter retraining. Written in `switching.py` and `DESIGN.md`.
- Tests: `sim/tests/test_scarcity_wage_short_run.py` (new, on built inputs). Rewritten because they pinned the old capped wage:
  `test_labour_core_substitute_wage.py` and `test_labour_core_skilled_ceiling.py` now assert on the heading wage (the cap) and that today's
  wage passes it; `test_labour_core_year.py` DemandTests asks for 60 carvers (the trade can fill that) where it asked for 120, which the
  trade never fills in the run, so a vertical bid now keeps the wage at the bid.
- Measured (wheat probe, shortened hidden spin-up `ROME_SPIN_UP_YEARS=3,2`, 5 years; a full spin-up does not finish in five minutes). Wheat
  price multiple of year 0, years 0 to 4: before 1, 0.21, 0.19, 0.17, 0.16; after 1, 0.75, 0.73, 0.74, 0.72. Iron bar: before 1, 0.77, 2.2,
  2.3, 3.2; after 1, 0.77, 1.7, 1.8, 1.4. Furnaceman hours hired (1e8): before 2.1, 1.7, 1.7, 2.4, 2.0; after 3.5, 2.2, 2.7, 2.6, 2.6.

## Update 2: the runaway wage and its bound

Probe (Rome, `ROME_SPIN_UP_YEARS=3,2`, every labour market, years 0 to 7, by wrapping `clearing.clear_one`): the unskilled
`labourer` wage of `work@morocco_07` went from 0.23 to 28 in year 3, with 190 thousand hours bid and the area's workers
offering none of their hours (they keep them for plots until the wage reaches the plot's worth). `ImportCosts`
asked whether the workers had the hours (they did), not whether they sold them, so it found no shortage and no cap; the
unskilled trade has no long-run cap. The wage then entered every skilled trade of the area through `unskilled_option`
(the reservation) and `trained_substitute_wage` (the long-run cap): furnaceman 28, baker 11, and they decayed over four
years. Furnaceman maximum over areas by year, before: 4.6, 5.1, 5.7, 28, 26, 22, 19, 7.8; baker: 5.2, 5.5, 5.1, 11, 14,
14, 12, 8.2. After: furnaceman 1.9, 1.6, 1.4, 1.2, 1.2, 1.1, 1.0, 0.79; baker 3.1, 3.6, 2.5, 2.4, 2.2, 1.6, 1.3, 1.2.

The three candidates, tested: (1) the cost-plus link is real in `producers.next_expectations` (the expected output price is
pulled toward the break-even price at last year's wages) but is not the runaway: with `REGRESSIVE_EXPECTATION_WEIGHT`
set to zero the maxima are the same. (2) A substitute is the bound: hands fetched from elsewhere, now counted by hours
sold. Switchers and the unskilled at a discount have no data and train for years, so they are not a short-run substitute.
(3) `maximum_wage` reads last year's wages and the expected price of the output; a bid does not read this year's wage.

Fix: `ImportCosts.hours_at` / `wage` count the hours sold at a wage (`hours_share_at`) in the area and in each area hands
come from, and find the lowest wage at which hours sold here plus hours fetched fill the bids (a bisection, since the
hours sold rise with the wage); no cap when the workers on the spot sell enough at the going wage already. Rule tests:
`HoursWorkersKeepBackAreNotHandsInHand` in `sim/tests/test_scarcity_wage_short_run.py` (the thin-trade-above-cap tests
there still hold).

Fixed (Update 3): thin markets of one employer whose bid carried the whole surplus of a run (piped water). Each trade of the
run claimed the run's surplus less the others' last wages, so the trades' claims added to more than the surplus. Now the
maximum wages of one run's trades share its surplus jointly (`sim/economy/labour_ceilings.joint_labour_ceilings`, called by
`sim/economy/producers._labour_bids`): each trade's maximum is its last wage scaled by the run's surplus over the last-wage
bill, so the run's hours at their maxima cost exactly the surplus, a paying run leaves every trade at least its last wage, and
a one-trade run keeps the whole surplus. Rule tests: `sim/tests/test_economy_joint_labour_ceilings.py`. The highest maximum wage
bid for a mason fell several-fold in the first years of a Rome game; a plumber's and a furnaceman's barely moved (their highest
bid comes from a recipe that is the trade's only labour or whose last wages already fill the surplus), so the plumber's wage
in the thin piped-water market is not closed by this change alone. Measure with a probe wrapping
`sim/labour/market/clearing.clear_one`.

## Left

- The run-up begins past year 12 (473 Update 9); the 20-year wheat path needs the full spin-up.
- The slow check that no trade pays above its trained substitute (`test_opening_floor_and_thin_trades`) is not in `sim/tests` under that name; a check that a thin trade in the opening does not quote a very high wage (434's potter and glassblower) against the heading wage has still to be written.
- Related-trade switchers do not read the scarcity wage.

## Open: the cost book prices own-account hours at a thin hired market's wage

473 Update 11 measured Rome's farmer wage at year 4 at more than ten times the unskilled wage, set in markets that hired few
hours (`economy_api.wages_by_trade_weighted`), and the making cost of farm goods followed it (olives priced far below that
cost). Most farm hours are worked on the household's own plots, not hired. Since this complaint lets a thin trade's wage rise
to its bids, the cost side should value a trade's hours at what an hour of it is worth to the people who work it (the hired
wage only for the share that is hired, the household's own reservation for the rest), not price every hour at the thin hired
market's wage. Not yet traced whether that is the whole of the farmer spike. Measure with the 473 Update 11 probe.

## Update 3: the import-wage bound weighs the hours that can be fetched (branch labor-market-economy-stability)

`ImportCosts.supply` gives the bound and the share of the hours wanted that can be fetched at it; `scarcity.short_run_ceiling` takes the
mean of the capped and the uncapped ceiling weighted by that share, so the bound grows with the hours that can come rather than switching on
once they cover the whole shortage. The wheat path over 20 years and the slow checks listed under Left are still not re-run.
