# Land never changes hands, and there is no landlord, tenant or lender

**Status:** partly - titles, collateral, foreclosure into tenancy, abandonment, partible inheritance, tenancy management cost, debt relief, tax farming, household bondage, a land buyer side (cohorts, firms and any actor), rent asks that follow the wage, leasing in the market, bonded hours worked for the creditor, a title sale market (holders short of money sell to buyers who value the rent at their own rate; the price gives lenders their land yield), confiscation and land reform (486), and a sourced concentration check on an economy where borrowers default are built; open: the fertility-by-holding channel (needs household demography), a concentration check on a full game

Reference (an outside design note, not code-aware): land concentration should come from harvest shocks and debt, not a typed
share. A smallholder short after a bad year borrows against the plot; a second bad year means default, the title passes to the
lender and the family stays as tenants or bonded labour. Land reform or a plague that makes labour scarce swings it back.
Taxes, rent and banditry drive abandonment of marginal land. The full log of what was built, with measurements:
`Complaints/reports/538-history.md`.

## What is wrong now

- **Title sales are cohort to cohort.** `title_sales_year.run` clears each tile: a cohort short of its cash target or in arrears offers
  the hectares that raise it at the rent over the rate cash costs it (the market loan rate); a holder with no need sells when
  the rent over its tile's last sale price is under what its money earns elsewhere. Buyers are the cohorts on the tile with cash above
  target, bidding the rent over their own rate (time preference plus expected inflation, the state's bonds where in reach). One price
  per tile, between the two valuations; the seller stays as the buyer's tenant. Firms and states hold titles and `title_sales.py` takes
  any actor's figures, but only cohorts are wired in as sellers and buyers (a firm's valuation of rent is not yet read here).
  Tile is the market area for households (`setup.labour_area`), so one clearing per tile is one per area. Not yet measured in a game:
  how many hectares change hands, and the prices, over a century (the orchestrator's measure: step a game and print `record.land.sale_price_by_tile`).
- **Fertility rising with holding size is not modelled** (one of Bekar and Reed's three channels, 2009, Oxford Economic and
  Social History 79). Households here do not have children; the channel needs household division in demography
  (`titles_inheritance.py`, retire: 538 household division in demography). Distress sales after harvest shocks and partible
  inheritance are built and tested as rules (`sim/tests/test_economy_land_concentration_rules.py`).
- **The concentration check on a village fixture is gone.** `test_economy_land_concentration.py` (BASELINE VALIDATION,
  `economy_land_concentration`) and `land_fixture.py` are deleted from `sim/tests/`; the rules remain. It ran households that borrow against
  their plots and default after a run of failed harvests, over an ensemble of shock histories, against the sourced band by
  denominator (`LAND_GINI_SOURCED` in `sim/tests/titles_concentration.py`). Han China and the Mexica have no band (no land Gini found in
  anything opened); no source gives a land top-decile share, so it is printed, not checked. A full game over a century
  where borrowing households default is still not run; print the fixture's path with
  the topic no longer exists, so nothing prints it.
  That a single failed harvest is carried by borrowing and moves no title, and that more households hit means a higher Gini,
  are claims about the multi-year fixture, not one function: they are no longer unit tests; measure them with the same command.
- **The fixture lands in the band only with partible inheritance on** (default `PARTIBLE_ESTATE_SHARE`); with estates that
  stay whole every history ends with the lender holding nearly everything (Gini near one), above every sourced row. The
  share is a labelled heuristic (retire: per-civilisation inheritance rule in data), so which side of the band a
  civilisation falls on is a data question, not settled here.
- **Bonded hours go to the creditor's works only where the creditor owns a producer bidding for that trade in that area**
  (`bondage_hours.py`); otherwise they stay in the market and the creditor takes the wage share as before. The hour's value
  off the debt is the cohort's reservation wage, not the creditor's value of it. The household default rule follows the credit
  market's arrears share (`credit.DEFAULT_ARREARS_SHARE`) while the founder's follows 589's arrears years, so the two agree on
  policy, not on timing.
- **Dividends still split by ownership share**, which is the income distribution; only land rent follows titles. Strata also carry
  a typed `property_share` (`data/civilizations/*.json`).
- **Supervision cost is a typed heuristic** (`titles_management.py`, retire: overseer staff and distance costs), as is partible
  inheritance (`titles_inheritance.py`, retire: household division in demography) bondage terms (`bondage.py`, retire: bondage contracts as data, with the inheritance share retiring to a per-civilisation inheritance rule in data) and the tax farmer's reach (`TAX_FARMER_REACH`, retire pointer 542 is a closed complaint; list `python3 sim/constants.py --burndown`).

## What it would take

- Household division in demography, so fertility can rise with holding size and estates divide by who has children.
- A full game long enough for borrowing households to default, with the elite-share range checked under CLAUDE.md 4.2
  and moved by a land reform and a labour shock. The range is a validation, not a target.
- One arrears rule for founder, firms and households (589).

## Research done and still needed

- Done: `Complaints/reports/research-household-wealth-and-land-concentration.md` section 2 gives the land Ginis by
  denominator that `sim/tests/titles_concentration.py` now holds: England 1279 about 0.59 with the landless left out and about 0.78 with
  them counted (Kumon 2021), a simulation of 120 years of land sales from 0.135 to 0.625 (Bekar and Reed 2009), Roman Egypt
  villages 0.37 to 0.52 and urban or absentee owners 0.62 to 0.76 (Scheidel 2019), enclosure parishes 0.65 to 0.82 with the
  landless counted.
- Still needed: a land Gini or top-decile share for Han China, Mexica nobles against calpulli land, and Rome (not income).
  Nothing opened gives one (Hicks 1982 and Carrasco were not reachable).

## Evidence for what is built

- Titles, collateral, foreclosure, abandonment, tenancy: `sim/economy/titles*.py`, `sim/tests/test_economy_titles.py`.
- Title sales: `sim/economy/title_sales.py` (valuations, clearing), `title_sales_year.py` (the year's step), `sim/tests/test_economy_title_sales.py`.
- Rent asks, leases in the market, the tools check: `sim/economy/land_tenancy.py`, `land_lease_year.py`; tests `test_economy_land_tenancy.py`, `test_economy_land_lease_year.py`.
- Buyers other than cohorts: `land_bid_year.actor_bids`, `firm_land_bids`, `take_up_bought` (any holder); `test_economy_land_buyers.py`.
- Bonded hours: `sim/economy/bondage_hours.py`; `test_economy_bondage_hours.py` (its `_scenario` file is gone).
- Concentration: `sim/tests/titles_concentration.py`, `test_economy_land_concentration_rules.py` (channels); the validation test and `land_fixture.py` are deleted.
- Land bid, seller floor and ground handling: `sim/tests/test_economy_land_bid.py`, `test_economy_land_seller_floor.py`, `test_economy_costless_run_stock_gate.py`, `test_economy_ground_not_queued.py`.
- Bondage: `sim/tests/test_economy_bondage.py`. Debt relief and tax farming: `sim/economy/debt_relief.py`, `tax_farming.py` (policy lever `sim/agents/policy_land.py`).
- Measure the land market in a game that has no crop buyer: step a Norse game (the scenario file this once named, `test_staff_closure_reopening_scenario.py`, is deleted) and print the clearer's stock, the remembered price and the titles of `sweden_01` each year; there a cohort's earning is the rent only, so a buyer's worth equals the seller's floor and little trades.

## Tried and failed

- A land seller's floor from `inventory.queued_holding_value` collapsed to nothing (the stock grew and expected sales decayed, so the discount ran to zero); replaced by the tile's rent capitalised at the rate.
- A first cut of the cohort bid that spent the cohort's whole cash left the poorest cohort short of its floors and defaulting; the bid now spends only the savings it would otherwise lend.
- The stock gate (`producers.runs_for_stock`) let a costless clearing run for ever on an empty sum; it now needs something else to sell.
