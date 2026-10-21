# A scarce skilled trade's wage is capped today at its long-run training cost

**Status:** open

`sim/labour/market/clearing.py` `clear_one` caps the year's wage of every trade at `trained_substitute_wage`: the unskilled
wage times the training premium. That is where the wage settles in the long run, once trainees have had time to qualify. A
trainee takes the trade's training years to arrive, though, so in the short run a trade whose employers bid far above the cap
should pay a scarcity wage (a quasi-rent) that draws its own workers' extra hours (`hours_share_at`) and switchers, and that
entrants weigh against the long-run cap.

Measured (473, Update 9): in Rome's opening, the furnacemen of `italy_02` are fully hired at a
wage of about 0.05 to 0.09 an hour while employers' bids carry a worth of 3.6 to 8.6. The trade's hired hours fall by more than
an order of magnitude over three years, the iron-bloom makers achieve a small share of their planned runs, and iron bar, iron
tools and then wheat (whose farms are starved of hours the same way) run away in price.

**What the fix should do.** The long-run cap stays on what entrants expect to earn after training. Today's wage clears against
bids, bounded by the cost of bringing a trained worker in (`ImportCosts`, a real short-run substitute). Write the rule test
first: a thin trade with bids far above the cap and few workers pays above the cap this year, its workers offer more hours, and
an entrant's graduation income stays at the cap. Then re-run the 473 wheat probe.
