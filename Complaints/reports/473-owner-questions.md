# Complaint 473: questions for the owner (branch spin-up-settles)

Written while working on 473 alone. Each question says what was found, why it needs a decision, and what the work
does in the meantime, so it can be answered without the session's context. Nothing here blocks the work: each
question has a default that the branch follows until answered.

## 1. What "settled" should mean for the spin-up

**What the check asks now.** `spin_up_settled` (sim/markets/spin_up_run.py `final_result`, sim/markets/spin_up_gap.py)
passes only if, over the last `SPIN_UP_MEASURED_YEARS` hidden years, every one of these moves less than `SPIN_UP_TOLERANCE` from one year to the next: the basket
price level, the interest rate (against `SPIN_UP_RATE_FLOOR`), real output, hired hours, producers' inventory value, unmet
food need (against `SPIN_UP_UNMET_FLOOR`), and each of the `SPIN_UP_WATCHED_GOODS` goods the opening basket spends most on.

**Why it matters.** That is a fixed point, not a steady state with noise. Among the watched goods are thin ones
(Norse `steel_noric_kg` falls to a small fraction of its opening price and moves by large shares a year; a per-year
probe of the spin-up shows it, and no committed command prints per-good prices by spin-up year). A deterministic
economy can in principle reach a fixed point, but an agent economy with lumpy producers usually settles into small
cycles in thin goods. CLAUDE.md 4.2 asks the baseline to be "a plausible draw", which reads more like a stationary
distribution than a fixed point.

**New evidence: the spin-up is chaotic.** A change that alters only the last digit of about one in seventy input bills
(the summation order of `close_kernel.close_rows`; merge d77138668, measured by instrumenting every call in a Norse run)
moved Norse's inventory gap by a factor of three and its price gap by a factor of three; installing numba mid-session
also changed Norse's trajectory although `sim/jit.py` says its settings keep a game reproducible (not checked further).
So the yearly change over the last few years of one trajectory is largely where the chaos happens to land, and a rule
change can be judged only by its effect on many perturbed runs, not on one.

**Proposal (not built).** Judge settling as stationarity of a distribution, which CLAUDE.md 4.2 already asks of the
baseline: run the trimmed stage for a longer window, and require for each quantity (a) no trend: the change between the
mean of the window's first half and its second half under the tolerance, and (b) bounded fluctuation: the spread of the
year-to-year changes under a stated bound; and run a few spin-ups whose opening differs in the last digit (a seed of
rounding) to show the result does not depend on the draw. Keep the fixed-point test as a reported figure.

**Question.** Should the check stay a fixed point (every watched quantity under the tolerance), or should it test
stationarity (no trend over the window, and fluctuation within a bound) for the thin goods? The complaint says "do
not weaken the settling tests", so the branch keeps the check as it is and tries to meet it. If the economy ends up
trendless but a few thin goods still cycle, I will report that and not change the check without your answer.

## 2. People on tiles with no farmland

**What was found.** In Norse, tiles with fertility exactly 0 (norway_02, norway_03, sweden_04, sweden_05, finland_03 and
the three Svalbard tiles) hold a sizeable minority of the people and most of the unmet food need (measured with a scratch probe of the
spin-up; no committed command splits hunger by tile fertility). They get no plot
hours at all (`household_hours_year.usable_plot_hours` returns 0 for fertility 0), their market areas sell out of food,
and their wages cover a small share of the food floor's cost. Raw millet meanwhile sits unsold in the fertile
sweden_01 area while bread, flour and cooked meal go unmet there.

**Question.** Is fertility 0 on those tiles intended (high fell, tundra, ice), with their people meant to live on
fishing, herding and trade? If so, the gap is that nothing carries food to them and nothing produces their food
locally; if not, it is a data question for the geography. The branch does not change the data; it fixes the money
leak first (below) and re-measures.

## 3. The opening's cash and savings once the own-plot floor is met first

**What was found.** The yearly household orders now meet the floors a household's own plot grew before sizing its budget
(merged on this branch). The opening (`opening_own.py`, `opening_demand_kernel.py`, `opening.py`) still applies the old
late cut, and it also gives households a "purse" equal to the money that late cut freed. Porting the yearly rule to the
opening (branch `opening-grown-floor-budget`, not merged) removes that purse. The households' savings then shrink, and
with them their store-of-value bids for silver and the ores, so on Norse the ore and silver markets stop trading at the
opening and the opening moves more in its spin-up, not less (`python3 sim/simulator.py opening-checks --civs norse_900ad`
on each branch). Measured in two steps: the rule alone breaks them; removing the purse code changes nothing further.

**Question.** What cash and saving should the opening give households? The old purse was a by-product of the leak, so
it has no economic reason behind it; but the opening's silver and ore demand rested on it. Options: (a) households open
with the cash balance they would hold at the stationary state of the yearly rule (their `cash_target` plus a year's
saving), derived from the same budget rule; (b) leave the opening as it is and accept that it disagrees with year one
(Complaints 545 and 607 stay open). The branch keeps (b) for now, since the spin-up only needs the yearly rule to be
consistent; the opening work is parked on its branch with this explanation.

## 4. Silver at parity, far above its making cost

**What was found.** Norse's money is weighed silver. Its design (`currency.has_mint` and `mint.py` docstrings) says the
metal is exchanged at parity, but the code paid sellers their ask, which fell with the price level; smelters then planned
on a thin margin and made far less than the coin wore away. The branch now pays parity (`mint_price.paid_in_metal`), and
Norse's money stock holds (`money_against_wear` passes). But silver now trades at parity, well above the bound of
`price_over_cost_coin_metal` over its making cost (`python3 sim/simulator.py opening-checks --civs norse_900ad`).

**Why it needs a decision.** For a money metal at a fixed price, a price far above making cost is what should draw more
mining until the best seams are taken and cost rises toward parity: that is the anchor of a commodity-money price
level, and it works over decades, not in the opening year. So the check may be asking the wrong thing of the coin
metal: the economically meaningful bound may be that silver's cost does not exceed parity (otherwise the mint gets
nothing) and that the gap is shrinking, not that the price sits near cost. Complaint 519 asks the same about silver and
gold.

**Question.** Should `price_over_cost_coin_metal` keep its band for a metal paid at parity, or test that parity covers
cost? The branch does not change the check.

## 5. The environment was missing numba

`requirements.txt` lists numba, and `sim/jit.py` runs the kernels as plain Python without it ("much slower"). This
session's cloud environment did not have it until an agent installed it mid-session; a Rome opening took about an hour
before and the five civilisations' opening checks took about half an hour together after. If the environment's setup
does not install `requirements.txt`, it should (`pip install -r requirements.txt`). `sim/jit.py` says its settings keep a
game reproducible with or without numba; that was not checked here.

The setup script to add to the "Full Access" cloud environment (its settings, Setup script); it was proposed from
the session but could not be approved from the phone app. It runs from the directory holding the checkouts, and was
tested there:

```bash
#!/bin/bash
if [ -d bootstrap-history ]; then pip install -q -r bootstrap-history/requirements.txt; fi
```

## 6. A new trade's crew that never runs never learns (Mexica's tools)

**What was found** (Mexica at d77138668, scratch probes; no committed command prints a producer's practice by year).
On main, Mexica had no maize, millet or cacao producers at all: every recipe with an iron tool was uncostable, and its
staple and coin-metal checks read cost estimates of goods nobody made. On the branch those producers exist and run,
but by hand, because almost no wooden tools are made. A new wooden-tool crew starts unpractised and
`practice.recipe_for` (sim/economy/practice.py) multiplies its hours several-fold; at that cost its plan's
`share_working` is nil, so it never runs, so it never practises, so the penalty never clears. Entry does not break the
trap: it subtracts the trade's nominal idle capacity (`entry.gap_beyond_spare`, `entry_margin.gap_at_entry_price`)
and sizes newcomers to last year's tiny traded volume (`entry_sizing.sized_runs`), and newcomers join the same crew.

**Question.** How should an unpractised crew decide to work? Options: (a) it plans at its practised hours and pays the
unpractised ones while it learns (an investment in practice, as an apprentice's first year is); (b) an entrant crew
starts at the practice of the trade's pool in the population when peers exist elsewhere; (c) leave the learning rule
and fix only entry, so it counts capacity that can actually be staffed. `Complaints/reports/research-how-a-brand-new-trade-forms.md`
is the background. The branch makes no change here.

## 7. Household work takes most of the labour year, so the hours a household sells are a small remainder

**What was found** (Norse, scratch probes logging one spin-up year by year; no committed command splits a cohort's year
into household work, plot, plan and sold hours). In the fertile Swedish area that swings most, household work
(`data/world/household_work.json`: cooking, water and fuel, cleaning and childcare, grinding) takes most of the cohorts'
whole year of hours, and the hours offered on the labour market are what is left (`labour_supply.hours_kept_at_home`:
the plot or plan hours plus household work, capped at the year). A remainder of two large numbers swings with any small
change in either: in several late spin-up years it reached zero, the fishers and farmers of that area sold almost no
hours, their output collapsed, and that is most of the year-to-year swing of real output and hired hours that keeps
`spin_up_settled` failing on Norse. Making the grind-or-buy-milled choice continuous (branch `grinding-share-continuous`,
not merged) did not help: the choice moves smoothly, but a small move in it still wipes out the remainder. Halving every
household-work task in a scratch copy roughly halved the year-to-year swings of real output and hired hours in an
eight-member ensemble (`python3 sim/simulator.py spin-up-trace --civ norse_900ad --stages --ensemble 8 --jobs 2`).

**Why it needs a decision.** The task hours come from time-use surveys of adult women (hours a day, 365 days a year, a
quarter of a household's people taken as adult women), and the model draws all of them from the same labour year
(a ten-hour day over the working days of `HOURS_PER_PERSON_YEAR`) that market work comes from. In those surveys the
housework is done on top of field and market work, over a longer day and every day of the year; so the model may count
it against a year that does not hold it. Which time budget household work comes out of is a modelling choice, not a
number to tune.

**Question.** Where should household work's hours come from? Options: (a) a person's whole waking year (every day,
a longer day), with market hours and household work competing for it, so the labour year is what is left after both;
(b) keep one labour year but count only the household members who do the work against it (the adult women's own hours,
not a quarter-person share of everyone's); (c) keep the rule and make household work respond to the worth of the hours
(the household cuts water, cleaning and grinding when the hours would sell dear), so the remainder cannot reach zero.
The branch makes no change to the data or the time budget until you answer; Norse will not settle without one of these.

## Where it stands (branch spin-up-settles)

Judged on eight-member ensembles (`python3 sim/simulator.py spin-up-trace --civ <civ> --stages --ensemble 8 --jobs 2`;
four members are too few, Complaint 473 Update 26), the late spin-up's median year-to-year move of each quantity:
- England and Han: hired hours, real output and the price level move by a little more than the tolerance; inventory
  value and the rate move by many times it. Rome (four members) is similar with larger moves of output and hours.
- Norse: every quantity moves by many times the tolerance, because household work leaves its people a small remainder
  of hours to sell (question 7).

What was merged since the last version of this note: a market-memory rule that drifted thin markets toward their making
cost was found and then the whole continuous memory blend reverted, since the rule before it measured better on Han
and England (Updates 26-27). Five further rules were made continuous on their own branches and measured; none is merged,
because none calmed the quantity it fed (Updates 27-29): `grinding-share-continuous`, `inflation-trimmed-mean`,
`stock-offered-in-tranches`, `durable-demand-continuous` (and the reverted blend).

So 473 is blocked on two answers: question 1 (what "settled" means: on England the remaining moves look like
stationary noise around a level, which a fixed-point test of every quantity cannot pass), and question 7 (household
work's time budget, without which Norse cannot settle). With those answered, the next steps are: build the
stationarity test on the ensemble if question 1 says so, change the time budget as question 7 says, then re-measure all
five civilisations; then questions 6 (Mexica's learning trap), 3 and 4.
