# Land never changes hands, and there is no landlord, tenant or lender

**Status:** partly - titles, collateral, foreclosure into tenancy, abandonment, partible inheritance, tenancy management cost, debt relief, tax farming, household bondage and a land buyer side (cohorts) are built; open: rent and lease terms following labour scarcity, confiscation and land reform, a concentration check on a full game, buyers other than cohorts, bonded hours leaving the labour market

Reference (an outside design note, not code-aware): land concentration should come from harvest shocks and debt, not a typed
share. A smallholder short after a bad year borrows against the plot; a second bad year means default, the title passes to the
lender and the family stays as tenants or bonded labour. Land reform or a plague that makes labour scarce swings it back.
Taxes, rent and banditry drive abandonment of marginal land. The full log of what was built, with measurements:
`Complaints/reports/538-history.md`.

## What is wrong now

- **Rent does not follow labour scarcity.** After a plague or war landlords should compete for tenants with lower rent and debt
  relief; the labour market moves wages with scarcity, but rent and lease terms (`sim/economy/land_lease.py`,
  `titles.settle_tenancies`) do not read it.
- **No confiscation or land reform, and no elite-overreach feedback.** When a few hold most land the state's taxpayers and
  recruits shrink; nothing lets that end in revolt or redistribution (486 stability).
- **The concentration check passes vacuously.** `sim/economy/titles_concentration.py` (slow topic `economy_land_concentration`)
  holds the top-decile share and the Gini within a wide band that is recalled, not looked up. The fixture economy never borrows to
  default, so titles do not move and the path stays at the opening's Gini. Do not read it as validation of the counter-forces.
  Print the path: `python3 -m sim.tests --slow --only economy_land_concentration`.
- **Only household cohorts bid for land.** `sim/economy/land_bid.py` and `land_bid_year.py` can be called by any actor but only
  cohorts are wired. A cohort with no hands to work a hectare is not modelled as a rent-only buyer. Ground goods are found as
  immobile goods a recipe makes from nothing (`land_bid.land_goods`); the data has no land marker.
- **Bonded hours stay in the labour market.** A bonded cohort still sells its hours and the creditor takes a share of the wages
  (`sim/economy/bondage.py`); the hours do not go to the creditor's own works (`sim/labour/labour_bondage.py`). The household
  default rule follows the credit market's arrears share (`credit.DEFAULT_ARREARS_SHARE`) while the founder's follows 589's
  arrears years, so the two agree on policy, not on timing.
- **Dividends still split by ownership share**, which is the income distribution; only land rent follows titles. Strata also carry
  a typed `property_share` (`data/civilizations/*.json`).
- **Supervision cost is a typed heuristic** (`titles_management.py`, retire: overseer staff and distance costs), as is partible
  inheritance (`titles_inheritance.py`, retire: household division in demography) bondage terms (`bondage.py`, retire: bondage contracts as data, with the inheritance share retiring to a per-civilisation inheritance rule in data) and the tax farmer's reach (`TAX_FARMER_REACH`, retire pointer 542 is a closed complaint; list `python3 sim/constants.py --burndown`).

## What it would take

- Rent and lease terms read the labour market's scarcity (hired share of offered hours, tenants' outside option), so a labour
  shock lowers rent before it lowers wages alone.
- A state policy lever for confiscation and redistribution of titles, with the unrest side in 486.
- A baseline run long enough for borrowing households to default (a full game, not the fixture), with the elite-share range
  checked under CLAUDE.md 4.2 and moved by a land reform and a labour shock. The range is a validation, not a target.
- Wire the land bid for firms and other actors; add a rent-only buyer.
- Bonded hours worked for the creditor, and one arrears rule for founder, firms and households.

## Research needed

- What land-concentration range and trajectory is plausible for pre-industrial agrarian societies, by civilisation (Rome, Han
  China, England 1300, Norse): the figures in `titles_concentration.py` are recalled. Sources: Scheidel and Friesen on Roman
  inequality, Allen on English and Chinese land, Domesday and hundred-roll holdings, Han census and land-tenure studies. No
  source has been opened for this yet.

## Evidence for what is built

- Titles, collateral, foreclosure, abandonment, tenancy: `sim/economy/titles*.py`, `sim/tests/test_economy_titles.py`.
- Land bid, seller floor and ground handling: `sim/tests/test_economy_land_bid.py`, `test_economy_land_seller_floor.py`, `test_economy_costless_run_stock_gate.py`, `test_economy_ground_not_queued.py`.
- Bondage: `sim/tests/test_economy_bondage.py`. Debt relief and tax farming: `sim/economy/debt_relief.py`, `tax_farming.py` (policy lever `sim/agents/policy_land.py`).
- Measure the land market in a game that has no crop buyer: step the Norse game of `sim/tests/test_staff_closure_reopening_scenario.py` and print the clearer's stock, the remembered price and the titles of `sweden_01` each year; there a cohort's earning is the rent only, so a buyer's worth equals the seller's floor and little trades.

## Tried and failed

- A land seller's floor from `inventory.queued_holding_value` collapsed to nothing (the stock grew and expected sales decayed, so the discount ran to zero); replaced by the tile's rent capitalised at the rate.
- A first cut of the cohort bid that spent the cohort's whole cash left the poorest cohort short of its floors and defaulting; the bid now spends only the savings it would otherwise lend.
- The stock gate (`producers.runs_for_stock`) let a costless clearing run for ever on an empty sum; it now needs something else to sell.
