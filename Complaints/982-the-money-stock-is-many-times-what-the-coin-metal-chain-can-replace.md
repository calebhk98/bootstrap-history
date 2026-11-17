# The money stock is many times what the coin metal chain can replace, so prices fall every year

**Status:** open - found tracing England's falling price level (Complaint 473 Update 31). The owner chose that households hold most of their wealth in other things than coin (question 8); opening without the hoard is not enough, because the yearly rules rebuild it out of the producers' coin (Update 32), so what a household does with income it does not spend is still to be designed

**What is wrong.** A money made of metal loses a share of itself every year (`metal_stock.COIN_WEAR_PER_YEAR`,
`METAL_GOODS_LOSS_PER_YEAR`, both unsourced). The stock rests only where the mint strikes what is lost. At every
metal-money opening measured the loss is far more than the chain makes, so the stock falls by about the whole loss
every year and the price level and the wage fall with it:

- England (struck silver): the placed silver makers give a small share of the yearly loss, most of it on a route with
  no ore (Complaint 981). Even the ceilings of England's galena and silver ore, all of it sent to the mint, give less
  than the loss.
- Norse (weighed silver): no maker of silver is placed at all.
- Han (struck bronze): the placed bronze capacity is a vanishing share of the loss.
- Mexica (cacao): the money has no loss, so this does not apply.

Measured by `PYTHONPATH=. python3 Complaints/reports/473-handoff/probes/unsited_probe.py <civ>` (the loss in units of
the backing good, the opening's demand for it and what each maker is placed to make) and, through a spin-up, the
`money_supply` rows of `ensemble_years.py`.

**Why the loss is so large: the stock is.** Through England's spin-up the households hold about two years of their
income in cash and the producers about a year of their sales, so all the money is more than twice a year's output at
its prices: it turns over less than once in two years (`series_probe.py`, then `money_ratios.py` on its output). The
households' spending rule (`households_buffer_stock.spending_budget`, after Eurace@Unibi) rests where cash, claims and
share wealth together are a target number of months of income; Eurace's payment account is a bank deposit, and here
it is coin, because a household has little else to hold. A stock of coin that large loses more metal a year than the
mines can raise. No source was opened in this session for the money stock or its turnover in any of these societies;
the figure to find is the stock of coin against yearly income (for England about the start date, the mint's output
and hoard evidence are the usual basis).

**Why it matters.** `money_against_wear` fails while the mint strikes less than the money loses. `spin_up_settled`
compares consecutive years (`spin_up_gap.state_gaps`), so a price level that falls steadily by less than the tolerance
a year passes it; an earlier version of this note said it could not, which was wrong. What the falling stock does is
move prices and wages every year, and in England's trace they fell by more than the loss in several years, because
the producers' cash drains while the households' does not (Update 32). Complaints 473, 970 and 961 wait on it.

**What the sources say** (`Complaints/reports/research-coin-loss-and-money-held.md`, opened in that session): the coin
stock of England about the start date was about a fifth of a year's income (Mayhew's series, read from a slide of
Munro's), and estimates of a coin stock's whole yearly loss run from the declared rate upward, with wear alone a
fraction of it. So the loss rate is not too high; the stock is about ten times too large against income.
`Complaints/reports/research-coin-metal-mines.md`: England's and the Norse's coin silver was mostly brought in by
trade, so no home chain replaced it; the hidden spin-up is a closed economy and has no such trade.

**What it would take** (question 8 asks which):
- households hold most of their wealth in something other than coin (land titles, plate, stores, stock, loans), so
  the coin they hold is what they need between pay and spending, and the producers likewise; or
- the opening sizes the money stock to what the placed coin-metal chain can replace and lets the price level follow;
  or
- the loss rates are sourced and turn out to be far smaller.
The first follows what people did and is the largest change. Whichever is chosen, the opening must also place a chain
that works (Complaint 981).
