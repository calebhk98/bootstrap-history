# Audit: what Rome's "unemployment" is made of

Branch `rome-unemployment-audit`, from `claude/labor-market-economy-stability-ueffy1` (sim unchanged from dac4691).
Saved opened Rome (`ROME_SPIN_UP_YEARS=3,2`), stepped 16 years with a probe that wraps `economy.clear_labour` and
`Economy._grow_own` and records offers, bids, sold/kept hours, people and the core's clearings per (trade, area)
(probe scripts: scratchpad `ua/probe2.py`, `ua/analyse.py`, `ua/exfarm.py`, `ua/open_probe.py`; not committed). Year n is the
output of the nth step, as in `rome_years.py`. Figures are the 1e10-scale hours of the saved economy; shares are the finding.

## What the number is

`macro_columns` reports idle over (hired plus idle) *hours*, where "offered" is the hours households sell at the wage the
market cleared at (`HourSupply.settle`): the year's 2000 hours per working person less household work, the plan and the
plot's wage-driven share. It is not a count of people: the core hires hours ("hours stand for workers",
`applications.py`), so there is no record of which person got hours. People can only be reported as person-equivalents
(people in a market times its unhired share), and "hired at all vs none" can only be answered per market, not per person.

### 1. People and hours, per working person (2000-hour year)

| year | unemp (hours) | whole year | household work | own plot worked | offered to market | hired | spare (no use) |
|---|---|---|---|---|---|---|---|
| 0 | 0.519 | 2000 | 1164 | 160 | 684 | 329 | 348 |
| 1 | 0.626 | 2000 | 1113 | 167 | 739 | 277 | 444 |
| 5 | 0.743 | 2000 | 1165 | 170 | 677 | 174 | 491 |
| 15 | 0.888 | 2000 | 1173 | 169 | 663 | 74 | 584 |

(Working people 5.7e7 of 1.23e8 people, flat over the 16 years. "Spare" is `ledger.spare_hours`: hours neither sold nor
used by the plot nor household work. Own plot + spare + hired + household work add to the year, less the plot-kept
hours counted inside own plot.)

Working population by trade, year 0 (share of working people): farmer 0.418, labourer 0.183, miner 0.062, mason 0.036,
spinner 0.035, weaver 0.033, furnaceman 0.032, fisher 0.028, potter 0.026, sailor 0.026, herder 0.025. Year 15: farmer
0.291, labourer 0.184, miner 0.090, furnaceman 0.073, fisher 0.047. "Farmer" is `labour_state.plot_trade`: the people
the opening placed as the ones "no employer needs" (`labour/market/opening.py`), who work their own land.

Where the idle hours sit:

| year | farmers: share of people | farmers: unhired share of their offered hours | farmers: share of ALL idle hours | non-farmer hours unemployment | non-farmer person-equivalent |
|---|---|---|---|---|---|
| 0 | 0.418 | 0.903 | 0.703 | 0.258 | 0.250 |
| 1 | 0.409 | 0.939 | 0.604 | 0.415 | 0.379 |
| 5 | 0.358 | 0.967 | 0.462 | 0.620 | 0.597 |
| 15 | 0.291 | 0.984 | 0.322 | 0.849 | 0.813 |

People in markets that hire nothing at all: 0.17 of working people at year 0 (farmer 0.120, sailor 0.026, charcoal
burner 0.011, carter 0.007, merchant 0.004), 0.22 at year 15 (farmer 0.172). Person-equivalent unemployment over all
trades: 0.52 / 0.61 / 0.73 / 0.86 at years 0 / 1 / 5 / 15, close to the hours figure, because hours per person offered
are nearly even across trades (about 680 to 790).

Answer to "what share of people get no wage work": cannot be read from the model. Upper bound: the 17 to 22 per cent
in markets where nothing was hired; the rest is spread as a fraction. Of a hired person's offered hours: the
market-level hired share (0.48 at year 0, 0.11 at year 15), uniformly, by construction of the hours-as-workers protocol.

### 2. How the offered hours are formed, and whether they are realistic

`labour_offers` gives each cohort a full `working_hours_per_year` (2000, `HOURS_PER_PERSON_YEAR`). `labour_supply.HourSupply`
removes `max(plan, plot-at-wage) + household work` (`hours_kept_at_home`); everything else is offered, with no leisure.

- Household work takes 58 per cent of the year (1164 hours per working person). It comes from
  `data/world/household_work.json`: per adult woman 0.73 + 1.8 + 2.6 + 1.8 hours a day (Burkina Faso time use, Ghana
  2009 diary), times a quarter of all people being adult women, times 2.15 people per working person. It is carved out of
  the 2000 hours. `research-working-year.md` finds 2000 inside the range of 1840 to 2920 hours of *work* (days worked
  times ten hours) in Denmark, England and Burkina-type sources; time-use diaries count household work *beside* paid and
  farm work, so carving it out of the same 2000 undercounts the time households have, or the 2000 is not a market-plus-farm year.
  This pushes offered hours down, so it is not why unemployment is high; if corrected the other way, offered hours and
  measured unemployment would rise further.
- The plot takes about 160 hours a person a year (8 per cent), because `usable_plot_hours` is only the floors the land
  held grows for the household's own needs; a farm household sells nothing grown beyond its floors. A pre-modern
  adult with a plot works it most of the year (research-working-year: 135 of 265 working days in agriculture for the
  Mendip farming miners; the sources span 180 to 290 days); here the plot absorbs 8 per cent of the year, and the 42
  per cent of workers the opening called plot-trade offer 662 hours each to the wage market where 10 per cent of
  those hours are bought. The plan hours are 0 at year 0 and 1.6e9 (about 3 per cent of the year) later.
- So the offered hours are not a "full working year less a small plot share"; they are a full year less household
  work, less a small plot. But of the 684 offered hours, 348 never find a use at all (spare), the leftover of a plot
  that can absorb only the floors.

### 3. Hours wanted at the opening

`opening_labour_market` places people in trades from hours needed divided by `opening_sold_hours_per_worker` (688), taking
the hardest trades first; those no employer needs become the plot trade (`idle_trade`), and `seeded_hours` adds hours
for trades no producer staffs (sailor 1.0e9, charcoal burner 4.5e8, carter 2.9e8, merchant 1.8e8: 2.0e9 in all,
5 per cent of offered). The resting contracts (`opening_resting.resting_labour_contracts`) hold the producers' needed
hours for the runs they expect to sell, paid at the opening wage.

| | hours | per working person |
|---|---|---|
| producers' hours needed, opening contracts | 3.28e10 | 575 |
| hours offered, year 0 | 3.90e10 | 684 |
| hours wanted (bids), year 0 | 1.92e10 | 337 |
| hours hired, year 0 | 1.88e10 | 329 |

So the opening is not sized to full employment: contracts cover 84 per cent of the hours offered at the opening
(Eurace sizes output so labour demand equals employment; here the recipe hours come from final demand, not from the labour
force). 16 per cent of offered hours have no contract at all (the plot trade's surplus, the seeded trades, and a mismatch
of hours per worker by trade: a labourer is contracted 920 hours against 684 sold). The opening assumes the
unhired hours go to the household's own plot (`opening_own.idle_hours`, `OwnPlots._cut` cuts the floor bids by what the
plot grows); the plot can use only the floors, so the other 348 hours a person are assumed worked but are idle.

Then year 0's own bids already fall 41 per cent below the resting contracts (3.28e10 to 1.92e10): miner 5.8e9 to
1.7e9, farmer 5.6e9 to 1.5e9, labourer 9.6e9 to 6.9e9 (the others hold). This is Complaint 961's unrealised planned runs.
Of year 0's 52 per cent: about 16 points are never contracted, about 35 points are the contracts producers drop in year 0,
about 1 point is the gap between bids and hires.

### 4. Over time: supply or demand

| year | offered | wanted | hired | unemp | wanted over offered |
|---|---|---|---|---|---|
| 0 | 3.90e10 | 1.92e10 | 1.88e10 | 0.519 | 0.492 |
| 1 | 4.14e10 | 2.04e10 | 1.55e10 | 0.626 | 0.491 |
| 2 | 4.34e10 | 1.47e10 | 1.35e10 | 0.688 | 0.339 |
| 5 | 3.76e10 | 1.00e10 | 9.64e9 | 0.743 | 0.267 |
| 10 | 3.87e10 | 5.63e9 | 5.40e9 | 0.861 | 0.146 |
| 15 | 3.73e10 | 4.24e9 | 4.16e9 | 0.888 | 0.114 |

Hours offered do not rise: they are flat to 4 per cent lower (the farmer share falls from 0.418 to 0.291 as people move
to wage trades, but they offer the same hours per head, and the working population is flat). Hours hired fall
by 78 per cent. In logs, hired over offered falls 1.46; hired contributes 1.51 of that and offered hours contribute
-0.05. About 100 per cent of the rise from 52 to 89 per cent is hours wanted falling (hired tracks wanted to within
a few per cent: vacancies are 2 per cent of hired at year 15). Supply is not the driver after year 0; year 0 is partly
(16 points) a supply-side artefact of the opening's placement.

## What the measure should be

Report three figures, not one, and drop "unemployment" for the hours one:

1. **Unemployment rate (people)**: person-equivalent unhired share among people who offered wage hours and are not
   own-account (not in the plot trade, whose offered hours are the residual after their own land). Function added:
   `diagnostics.person_equivalent_unemployment(rows of (people, hours offered, hours hired))`, rule test
   `sim/tests/test_person_equivalent_unemployment.py`. Rome: 0.25 / 0.38 / 0.60 / 0.81 at years 0 / 1 / 5 / 15 over
   non-farmer markets; still far from a few per cent, so the gap is real wherever the plot trade is put.
2. **Unsold-hours share** (the current column, renamed "hours unsold"): includes hours that households put to their
   plots anyway.
3. **Spare-hours share**: hours that neither sold nor found a use (`spare_hours`), 0.17 / 0.22 / 0.25 / 0.29 of the
   year, the true idle time; plus under-employment (hired over offered for those hired).

A true labour-force rate needs the core to carry which workers were hired; today it carries hours.

## What makes the people rate high, and three changes

1. **Demand collapse (accounts for the whole rise to 89 per cent): Complaint 961.** Hours wanted fall 78 per cent in
   15 years and 41 per cent in year 0, where producers drop runs their inputs cannot supply. Size the opening to
   what inputs in reach can supply, and let the year plan within input reach (parked patch
   `961-plan-within-input-reach.patch.txt`), then re-measure. This brings the opening's contracts and year-0 bids
   into line, which also removes the 35 points that the first year sheds.
2. **The plot trade is 42 per cent of people with nothing to do with their hours.** The opening makes a surplus-people
   trade "who work their own land", but `usable_plot_hours` gives that land only the household's floors (160 hours a
   person), so 348 hours per person a year are in neither wage work nor plot work. Let own land produce beyond the
   floors where an hour on it beats the wage (the same marginal rule `plot_hours_kept` already uses, with the sale of
   the surplus as a source of income) so a farm household's hours go to its farm, not to the labour market. No
   outcome is hardcoded; the plot's output elasticity and land held decide.
3. **Opening placement and household-work accounting.** Place people from hours per worker *by trade* at the wage they
   sell at (a labourer's contract of 920 hours against 684 sold overstates demand per head and hides the shortage),
   seed trades with no producer (sailor, charcoal burner, carter, 2.0e9 hours) only where an employer exists or a
   carriage/merchant channel hires them, and decide whether household work is carved out of the 2000-hour year (as
   now) or beside it. The last one lowers or raises offered hours by up to a half and should be settled before any
   target for the unemployment rate is read.

Open: whether the model should hold people individually in the labour core so the people-based rate is a count, not a
person-equivalent; that is a core change and not proposed here.
