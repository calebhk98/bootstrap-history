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

## Left

- The run-up begins past year 12 (473 Update 9); the 20-year wheat path needs the full spin-up.
- The slow check `test_opening_floor_and_thin_trades` (no trade pays above its trained substitute) reads today's wage and is expected to
  fail or need rewriting to the heading wage; not run here. A thin trade in the opening could again quote a very high wage (434's potter and
  glassblower): check with that test.
- Related-trade switchers do not read the scarcity wage.
