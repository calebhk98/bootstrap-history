# Model run: Lengnick 2013 baseline (newwayland/baseline-economy)

**Status: code read, NOT run.** The run was blocked: the permission classifier refused to execute the downloaded
code (a driver script importing it, in a venv with `mesa==0.8.8.1`, which installed fine). So there is no measured
unemployment series below, and nothing here is a result "from the run". Everything is from reading the code that
would run. To get the series, someone with authority must allow running it (commands at the end).

## Source and licence

- Code: https://github.com/newwayland/baseline-economy, HEAD d9f5cc3 "Update test workflow", cloned to
  `/tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/models/lengnick/baseline-economy`.
  Python + Mesa 0.8.8.1, about 1,700 lines. It is a third-party replication, not the author's Java code (CoMSES lists
  the original as "Model code not found").
- Licence: AGPL-3.0. Running locally is fine. We must not copy code into our repository; ideas only.
- The repo's own `notes/issues.md` lists 20 places where the paper is silent or ambiguous and the choice made. That
  file is the replication's divergence record; points marked (R) below are choices of the replicator, not the paper.

## Rules in the code (file:line in `BaselineEconomy/`)

Time: a tick is a day, 21 days a month (`model.py:36`, `schedule.py`). Month start runs all firms then all
households; each day households buy before firms produce (`schedule.py:64-74`), so households only buy earlier output.

**Labour supply.** Every household offers exactly 1 unit of labour per day, fixed (`model.py:35`, `household.py:272`);
no hours choice, no participation choice, everyone is in the labour force. Reservation wage starts 0
(`household.py:14`). Unemployed: multiplied by 0.9 each month (`household.py:261-262`). Employed: raised to
`max(reservation, current wage)` each month (`:264`). So it ratchets up with pay and only falls in unemployment. Not
tied to subsistence or savings.

**Labour demand.** Not planned output. The firm compares inventory with `current_demand`, the units sold last
month (`firm.py:317-329`, `:210`): floor 0.25 x demand, ceiling 1.0 x demand (`:48-49`). Per month
(`manage_workforce`, `firm.py:179-199`):
- inventory below floor: open a vacancy, but only if no worker is on notice (`:187`); if one is on notice the notice is
  cancelled instead and no vacancy opens (R, issue 6).
- a worker on notice is fired at the next month start (`:191-192`).
- inventory above ceiling: cancel the vacancy and put one random worker on notice (`:196-199`).

Hiring and firing caps: at most one vacancy and at most one dismissal per firm per month; symmetric. With about 10
workers per firm that is up to 10% of staff per month either way. No speculative hiring: a firm with zero stock,
demand and workers cannot recover (issue 12). A firm with no workers produces nothing (`:232`), sells nothing, and
opens a vacancy only if inventory is under 0.25 x last demand = 0, so `inventory < 0` is false: it is dead.

**Production.** Output = 3 x labour units per day (`firm.py:65,74-78`); no capital, constant returns.

**Matching.** Household-driven (R, `notes/issues.md`, "Firms will hire the first Household..."). At month start a
household looks for work if unemployed, paid under its reservation wage, or with probability 0.1 anyway
(`household.py:381-389`). Unemployed sample 5 firms uniformly at random, employed 1 (`:185-193`); it takes the
first firm that has an open vacancy and pays more than the reservation wage (employed: or more than the current
wage) (`:397-410`). Firms never choose among applicants; no queue; a vacancy takes one hire (`hire` clears the flag,
`firm.py:363`). Household order is reshuffled daily, so who is first is random.

**Wage setting** (`firm.py:164-177`). A firm with an open vacancy at month start raises its wage by U(0, 0.019)
(`:44,85`). A firm whose vacancy has been closed for 24 consecutive months (`gamma`, `:41`; counter `:271-279`) cuts it
by U(0, 0.019). Otherwise wages do not move. No link to unemployment as such, only to the firm's own vacancy history.
In crisis (`pay_wages`, `:237-253`) the wage is cut to what liquidity affords, to zero if liquidity is below the head
count, and it stays cut. Wages are whole integers.

**Prices and money.** Price rises up to 2% if inventory is below the floor and price under 1.15 x marginal cost, falls
if above the ceiling and over 1.025 x marginal cost, tried with probability 0.75 (`firm.py:201-222`). Marginal cost =
wage / (3 x 21) (`:295-301`). Money is closed: firms keep a 10% wage-bill buffer and pay the rest out as dividends in
proportion to household liquidity (`:255-269`, `schedule.py:81-85`). Household consumption = (liquidity / mean
price) ^ 0.9 (`household.py:57-69`).

**Initial conditions** (`batch_run.py:49-57`, config defaults): 1000 households, 100 firms, nobody employed at the
start (`household.py:104`), household liquidity 3100, firms 0, price 25, wage 68 per day, firm inventory 0, expected
demand 1. So the start is **not** sized to full employment; it starts at 100% unemployment with money and wages set by
hand ("Value not stated in paper", `firm.py:14-35`). Firms with inventory 0 and demand 1 are below the floor, so all
open a vacancy in month 1.

## Measured series

Not available (run refused). Expectation from the code only, unverified: one vacancy per firm per month means at
most 100 openings a month and unemployed households sample 5 firms each, so the early fill from 100% unemployment
should be fast; the long run depends on the stock/demand band and the 24-month wage cut. The paper reports
unemployment of a few percent as typical; that is the paper's claim, not something measured here.

Parameters the paper treats as decisive: price flexibility `upsilon` (0.02) and wage flexibility `delta` (0.019),
with `gamma` (24) the wage-cut patience (`firm.py:41-57`). Not varied, since nothing was run.

## Where code and documentation differ

All of `notes/issues.md`. Those bearing on labour: employed workers switch for any higher wage, the unemployed only
above reservation (issues 4-5); notice/vacancy interaction (6-7); whether a vacancy persists across months (8; code:
it persists, `firm.py:276-277`); initial reservation wage, liquidity, employer and wage level all invented. A comment at
`firm.py:183` says "If inventory is too high" above a branch that tests too low (comment error only).

## Comparison with our repository

Ours: labour core `sim/labour/market/` (DESIGN.md, `applications.py`, `asks.py`); employers' bids from
`sim/economy/producers.py` `plan` (line 282) through `sim/economy/labour_bids.py` `sloped_bids`.

| Lengnick rule | Ours | Difference |
|---|---|---|
| Vacancy opens when inventory is under 0.25 x last month's sales; one per firm per month; stock over 1.0 x sales puts one worker on notice | `plan` sizes runs, hence hours, from expected revenue against variable cost at live wages and cash (`producers.py:282-306`); `sloped_bids` cuts that into 4 tranches | We have no inventory-triggered hiring and no per-period cap on hiring or firing: hours are re-planned each year. A firm whose planned margin is negative bids 0 (`Plan(0.0)`). Theirs is a feedback loop on realised sales and stock; ours is a forward plan with sales entering only through expected prices. |
| One head hired or fired per firm per month | Each search round every employer dismisses a random share and reposts; 12 rounds a year (`DESIGN.md`, `asks.py`) | Both bound churn; ours by a share, theirs by one head. |
| Reservation wage ratchets up to current wage, falls 10% a month unemployed, no floor | Ask starts at subsistence + danger pay, floor is the own-plot value (`labour_ask_floor.py`); falls with unsold hours, rises on unmet demand; 1% cut per failed round (`asks.py`) | Theirs has no floor, so pay can go to zero. Ours has a subsistence/plot floor and no ratchet with pay. |
| Wage up U(0,1.9%) a month while a vacancy is open; down only after 24 months of no vacancy | Up 1% a round while vacancies stay open; hired workers' contracted wages are not lowered (`DESIGN.md`) | Close in spirit; theirs has a slow downward channel for hired workers, ours has none. |
| Household tries 1 to 5 random firms, first open vacancy above reservation wins | Searchers apply to a bounded number of employers whose offer meets their ask and take the highest | Same family; ours takes the best offer, theirs the first. |
| Everyone offers 1 unit; no inactivity | Hours per worker per year; own-plot hours kept back (`households_own.py`) | Ours has a non-market alternative; theirs has none. |
| Start at 100% unemployment, hand-set money | Start from the historical state | Theirs does not test a full-employment start. |

What Lengnick has that we lack: a demand-feedback hiring trigger tied to realised sales and stock; one-head caps per
period; wage-cut patience counted in months. What we have that it lacks: wage floor, trades and skills, training,
migration, a plan from margins.

Code-derived observation, not measured: in Lengnick a goods-market shortfall opens vacancies directly. In ours the
goods market reaches the labour market only through the planned margin; if expected revenue is under variable cost the
bid is 0 (`producers.py:299-300`). I did not check how that interacts with the 52% to 90% unemployment.

## To finish (needs permission to run the downloaded code)

```
M=/tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/models
$M/lengnick/venv/bin/python -I $M/driver/run.py $M/lengnick/baseline-economy <seed> <months> <out.json> ['{"delta":0.0095}']
```
The venv (`mesa==0.8.8.1`) exists there, but the driver script `$M/driver/run.py` was never created (the write was part
of the refused command). It must record per month: unemployed, vacancies, notices, mean price, mean wage.

## Measured run (orchestrator, after the owner allowed running the code)

newwayland/baseline-economy at d9f5cc3 in a venv with mesa 0.8.8.1, the parameters of its `batch_run.py` (1000
households, 100 firms, household liquidity 3100, firm liquidity 0, price 25, daily wage 68), 21 steps a month, run with
`-I` (runner `scratchpad/scripts/run_lengnick.py`, not committed). Unemployed share of households by month:

| Seed | Months 0-24 | Months 24-120 | Months 120-1200 |
|---|---|---|---|
| 1 | mean 0.195 (from 0.90 to 0.00 by month 10) | mean 0.015, max 0.087 | mean 0.004, max 0.034 |
| 2 | mean 0.196 | mean 0.014, max 0.094 | mean 0.004, max 0.043 |
| 3 | mean 0.194 | mean 0.015, max 0.087 | mean 0.004, max 0.033 |

From full unemployment the economy reaches full employment in about ten months (one hire per firm per month) and stays
within a few per cent of it for a hundred years, with no wage floor (households accept any wage above a reservation
that falls while unemployed) and labour demand driven by inventory against sales.
