# Stationary opening: calendar, constraints and remaining work

Status: partial implementation for GitHub issue #61. The durable-stock boundary
is implemented and tested (`sim/tests/test_durable_stationary_state.py`). The
opening income is a root find for zero net saving (`sim/economy/opening_income.py`)
and the stationary quantities of one repeated year are in
`sim/economy/opening_stationary.py`; the coupled opening solver described below
is not implemented. No shipped opening should be regenerated on the strength of
the durable correction.

## The state to solve

Use the start of planning, after the preceding year's close, as the boundary.
Fix population, technology, resource access, institutions and weather inputs.
The state includes inventories by owner and place, plant, workforce, land
titles and tenancies, cash, creditor/debtor contracts, and agents' expectations.
Prices, wages, rents, income and the interest rate are unknowns, not independent
inputs to a later reconciliation.

Stationarity means that a complete quiet year returns these economically
meaningful stocks and expectations to their starting values. A phase need not
leave them unchanged: buying increases a durable holding and wear reduces it.
Each phase must instead map its solved incoming boundary to its solved outgoing
boundary. Calendar counters and cumulative audit flows are not stationary
stocks. Debt must be compared by remaining term and creditor/debtor exposure,
not by contract identifier or absolute maturity date.

The macro settling report is a necessary validation, not proof of these
identities. Aggregate prices can stay still while a household loses its land
or a producer exhausts an input stock.

## Required coupled equations

| Boundary or choice | Condition | Existing rule to reuse |
| --- | --- | --- |
| Household time | Available hours equal hired hours, own-plot hours, household work and unused hours; plot use is bounded by the land actually worked | `household_work_year`, `households_own`, `titles_worked`, labour core |
| Household goods | Purchased plus home-grown goods meet chosen consumption and replacement, subject to cash and physical supply | `households_orders`, `year_goods`, `households.consume` |
| Producer goods | Output and incoming goods cover sales, intermediate use, plant replacement and losses, leaving inventories unchanged | `producers`, `year_goods`, `inventory` |
| Capacity | Replacement equals physical wear; planned runs obey land, labour, input, site and finance constraints | `opening_runs`, `sites`, `land_market`, producer planning |
| Household income | Wages for actual hires plus the actual distribution of rent, profit and net interest equal the income used in demand planning | labour settlement, `ownership`, `close_agents`, lending |
| Money | Every payment has a payer; net coin creation equals coin loss; each agent's cash returns to its boundary value | `accounts.Book`, `mint`, `metal_stock`, `money_audit` |
| Credit | New principal replaces repayment and write-offs; lender claims and borrower obligations reconcile; rates meet current participation rules | `credit`, `credit_claims`, `lender_ask`, `lending` |
| Land and equity | Valuation and title ownership used in saving decisions agree with the assets and income streams actually seeded | `titles_value`, `equity`, `CreditView` |
| Expectations and entry | Expected sales, costs, income, inflation and spending agree with realised values; entry, exit and inheritance have no net unexplained drift | producer/household close, `entry_year`, `titles_inheritance` |

Gross saving can fund replacement investment in a stationary economy. Buying
existing land or extending a loan transfers purchasing power between agents;
it is not additional physical investment for the economy as a whole. Land
wealth can satisfy a household's desired wealth stock, but a land transaction
cannot simply be added to aggregate final output to repair an income shortfall.
The seller's cash and subsequent decisions must be included.

## Implemented durable boundary

The household's desired serving stock is its expected annual service flow
times service life. `year_close.wear_and_spoilage` computes both losses on the
same serving-stock snapshot. The opening therefore seeds that stock after
those losses, and annual orders buy only the gap back to the serving stock.
They do not add another wear allowance to an already worn holding.

During opening income and capacity sizing, the stock has not yet been seeded.
`goods_orders(stationary_durables=True)` uses replacement demand at the solved
durable boundary. Seeding separately derives the whole serving stock. The
ordinary yearly rule has no opening-mode dependence.

Direct checks, including spoilage and the opening-to-orders connection:

```bash
python3 -m unittest sim.tests.test_durable_stationary_state
python3 -m unittest sim.tests.test_economy_durables_budget sim.tests.test_economy_households sim.tests.test_economy_service_lives
```

This is conditional on unchanged service demand and affordable replacement.
It does not assert that opening incomes, relative prices or savings plans are
stationary. The normal budget caps still bind.

## Land rent at the opening

The opening sets each tile's land rent by the year's own rule (`opening_rent.settle`, which runs `land_market.post_rents` on the
producers placed), so year one sees the rent it was sized for. A hectare's rent is a share of what it grows, so the prices of the recipes
that take land are raised until revenue pays cost and rent (`opening_rent.covering_prices`, solved in `opening._with_covering_prices`
until they stop moving: one full household solve, then each pass reopens the economy at the covered prices with the households' settled plans, `opening._reopen`). The rent is paid to the households that own the land and counts in their property income
(`opening_rent.property_income_with_rent`); the rent and profit part of the income figure is seeded as the first year's property income
(`opening_income.property_income_of`). Measure: `python3 sim/simulator.py spin-up-trace --fixture stationary --years 50`.

## Why the current income iteration is insufficient

`opening._settle_income` solves for a scalar income (a root find for zero net
saving) against final demand while
prices, wages and the rate are fixed. It runs before producers, their equity,
cash, credit and stores are seeded, using `YearView`. Annual household decisions
instead read `CreditView`. The two calls therefore face different balance
sheets, even at the same proposed income. A scalar root can exist at
subsistence without solving employment or the desired wealth distribution.

The opening now retains the cohort-specific hearth and household-work basket.
That does not solve the hired/own hours split: the yearly decision
still has to agree with the split assumed in opening production and demand.
Likewise, land-valuing helpers are not evidence that land wealth is already
included in household spending: `CreditView.equity` currently reads firms.

## Solver implementation sequence

Build phase-boundary residuals first, using the existing pure rules. Identify
each residual by rule, agent, good or trade, tile and unit. Check physical
feasibility and accounting identities separately from numerical convergence.
Use unit-aware absolute and relative numerical tolerances; the macro settling
bounds are not tolerances for an unbalanced ledger.

Solve the small fixture jointly for hours, output, inventories, balance sheets
and expectations. Eliminate quantities with exact identities where possible,
as for the durable boundary. Treat nonnegative stocks and binding land, labour,
site and cash constraints explicitly. Alternate the physical allocation block
and the balance-sheet/price block only while checking the residual of the
complete year; convergence of one block alone does not count.

Seed a candidate record from the solution and run the ordinary phases without
any stationary-mode overrides. A residual must identify the first rule whose
output disagrees with its solved boundary. Do not overwrite the result with
the requested state or stop a burn-in at a convenient year.

Then expand to the historical setups and validate the full traces below and
multiple seeds. If a positive feasible stationary solution cannot be found,
report the unresolved equations and binding constraints. Non-convergence alone
does not prove that no solution exists. Where turnover is intrinsic, specify
and test an invariant distribution rather than quietly claiming an exact
per-agent fixed point.

```bash
python3 -m sim.tests --slow --only real_output_measure,real_output_wiring
python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60
python3 sim/simulator.py spin-up-trace --civ england_1300 --years 60
python3 sim/simulator.py spin-up-trace --civ mexica_1500 --years 60
```

Apply `sim.economy.settling.settling_report` to each complete trace. Keep its
existing thresholds. The results and full-suite failures belong in the issue
and PR measurement record; this design does not claim those validations pass.
