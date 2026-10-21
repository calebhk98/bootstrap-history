# Land never changes hands, and there is no landlord, tenant or lender

**Status:** partly - titles, collateral, foreclosure into tenancy and abandonment, the baseline range check, the counter-forces (partible inheritance, tenancy management cost, state debt relief), tax farming and household bondage are built; still open: labour scarcity moving rent and lease terms, elite overreach and confiscation or land reform (486, 542), and a concentration check on a full game (the fixture economy never concentrates, see below)

Reference (an outside design note, not code-aware): land concentration should come from harvest
shocks and debt, not a typed share. A smallholder short after a bad year borrows from a landowner or
financier at ancient rates, pledging the plot; a second bad year or a conscripted son means default,
the title passes to the lender and the family stays as sharecroppers or bonded labour. Land reform
or a plague that makes labour scarce swings it back. Taxes, rent and banditry drive abandonment of
marginal land (agri deserti).

## What the code does

- **Ownership is the income distribution.** One global `GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN`
  (`sim/world/demand.py`) sets each tile's equal-population income classes
  (`sim/economy/households_cohort.py`), and a class's `ownership_share` is its income share. The
  richest class on a tile is its landowner (`sim/economy/ownership.py`). Strata add a typed
  `property_share` (`data/civilizations/*.json`, `sim/agents/stratum_year.py`). No title is held or
  moves.
- **Peasant credit has no collateral.** Households borrow only for a subsistence shortfall
  (`sim/economy/households_credit.py`), with zero collateral, from pooled savings
  (`sim/economy/credit.py`). Default books a loss to the lender (`credit.py`); no land, tenancy or
  bondage follows. `debt_bondage` is a carried flag (`sim/agents/cast.py`).
- **Rent is not a harvest share.** It is a Ricardian rent per hectare cleared by tile
  (`sim/economy/land_market.py`, `land_lease.py`, whose docstring names the missing lease book).
  Households pay no rent on the plots they work.
- **No rentier, financier or tax farmer actor.** Rent reaches strata as property income
  (`sim/agents/group_rent.py`); nobody lends except pooled savings and the state reserve; no revenue
  is farmed out to bidders.
- **No abandonment.** Farmed area only grows (`sim/labour/labour_allocation.py`); migration is
  wage-driven (`sim/labour/market/migration.py`), not driven by yield after tax and rent.

## What it would take

- Plot titles per tile held by actors, sold, pledged and foreclosed.
- Collateralised household loans; on default the title passes and the household becomes a tenant
  (a lease paying a harvest share or fixed rent) or bonded (`sim/labour/labour_bondage.py`).
- Landowner and financier actors under the general actor rule (founder, firm, state alike), and tax
  collection let to bidders as a state choice (see 475).
- Land left uncultivated when the yield after tax and rent is below subsistence, with the household
  migrating or joining a bandit group (486 stability).
- A baseline check under 4.2: elite land share over a long run lands in a plausible range and moves
  after a land reform or a labour shock. The range is a validation, not a target.

## Counter-forces (second note from the same source)

Foreclosure alone would drive elite land share to all of it. The same model needs the forces that
pull it back, each a mechanism rather than a cap:

- Supervision: a landowner's cost of overseers and lost effort rises faster than the land held, so
  far or large holdings pay less than they yield and are let or sold.
- Inheritance: estates divide among heirs where the society's rule is partible (Rome, Greece, Han
  China), which needs owners who die and have children; household cohorts here do neither.
- Labour scarcity: after a plague or war, landlords compete for tenants with lower rent and debt
  relief. The labour market already moves wages with scarcity; rent and lease terms would have to
  follow it.
- Elite overreach: when a few hold most land, the state's taxpayers and recruits shrink, which can
  end in revolt or confiscation and redistribution (486 stability, 542 state choices).

## Resolution

- `record.titles` (tile -> holder -> share of the land) is seeded at the opening from the cohorts' ownership
  shares, so rent flows as before until a title moves. A holder is any actor id (cohort, firm, state, seat).
  Producers' rent is split by title, not by ownership share (`ownership.spread`).
- A household's request pledges its whole free title on its tile (`lending._pledging_title`); the pledge rides
  the loan (`collateral_tile`, `collateral_share` on the contract) and lowers the risk premium through the
  capitalised rent. Rent is the cleared land rent; a tile no producer rents gives a title no value.
- Default passes the pledged share from borrower to lender (`titles.foreclose`); the lender's credit loss is
  reduced by the collateral's value; the borrower stays as a tenant (`record.tenancies`) and pays the lessor
  the tile's rent on that share through the ledger each year (`titles.settle_tenancies`, from
  `land_market.settle_year`).
- A tenant more than a year's rent behind has left the land: the lessor's title on it goes back to nobody
  (abandonment). Rent from producers then goes to the remaining holders.
- The one read of a holder's land wealth is `titles_value.title_wealth(tiles, record, holder, rate)`, exported
  as `sim.economy.api.title_wealth`; the rate is `titles_value.capitalising_rate(live_rate, opening_rate)`.
  `goods_orders` does not read it yet (526).
- Tests: `sim/tests/test_economy_titles.py` (bad harvests concentrate titles through default and a good run
  does not; the defaulted family pays rent; abandonment; seeding; save round trip).

Built after the first cut (each with a quick test topic):

- Range check (`sim/economy/titles_concentration.py`, slow topic `economy_land_concentration`): the top-decile
  share of holders and a Gini over holders' hectares, asserted to stay within a wide pre-industrial agrarian band
  (the band is recalled, not looked up; the test says so). Measure the path with
  `python3 -m sim.tests --slow --only economy_land_concentration` (the test prints it). The fixture economy
  never borrows to default, so titles do not move and the path is flat at the opening's Gini: the check passes
  vacuously until a full game with household borrowing is run through it. Do not read it as validation of the
  counter-forces.
- Partible inheritance (`titles_inheritance.py`): households do not die or divide here, so a labelled
  transitional rule (retire: household division in demography) passes a generation's share of the land a cohort
  holds above its opening ownership share to the tile's cohorts that hold less than they opened with, in
  proportion to the shortfall. Pledged land stays; a tenant who inherits from its own lessor holds that land
  outright (`titles.pass_title`). Run once a year after loans are serviced.
- Management cost (`titles_management.py`, in `titles.settle_tenancies`): a lessor's stewards take a share of
  every tenancy's rent that rises with the number of other tenancies it holds (a lone tenancy is free), paid to
  the tile's poorest cohort as `steward_pay` (not property income); where the cost eats all the rent the tenant
  holds the land outright. The rate is a labelled heuristic (retire: overseer staff and distance costs).
- Debt relief (`debt_relief.py`, lever `sim/agents/policy_land.py`, port `sim/engine/economy_port_land.py`): a
  state's decision policy is offered the tiles where households owe (`debt_relief` decision); the tiles it picks
  reach the economy as `YearInputs.debt_relief_tiles`, where the tiles' household loans are cancelled (the
  lender books the loss, no title moves) and tenants' rent arrears are forgiven. The default policy values it at
  nothing, so only a player's or a mod's policy chooses it.
- Tax farming (`tax_farming.py`, `YearInputs.farmed_forms`, `policy_land.farmed_forms`, collection in
  `year_close.money_taxes`): the state names money forms to farm for the year; any actor with cash bids the form's
  base of last year at its own reach, discounted a year and capped by its cash; the best bid at or above the
  state's own expected take (discounted likewise) wins, pays the state up front, and collects through the ordinary
  assessment (`taxes.assess`) at the farmer's reach (labelled heuristic `TAX_FARMER_REACH`, retire 542). A form
  needs a year of history before it can be farmed (`record.tax_history`, saved).
- Bondage (`bondage.py`, `EconomySetup.debt_bondage_years`, `Sim.debt_bondage_term_years`): the founder's default
  and every household cohort's go through one rule for whether and how long (the society's `debt_bondage` and
  `bondage_years`). A cohort whose default leaves it with no title enters bondage to its lender for the loss the
  collateral did not cover (`record.bondage`, saved); each year the creditor takes the owed share of the cohort's
  wages (the product of the bonded hours: the cohort still sells its hours) as far as its cash goes, which comes
  off the debt and the creditor's credit loss, until the debt is worked off or the term served. Not built: the
  bonded hours do not leave the labour market for the creditor's own works, and the arrears-years rule of 589
  (`borrowing_arrears`) is the founder's and firms'; the economy's household default still follows the credit
  market's arrears share (`credit.DEFAULT_ARREARS_SHARE`), so the two rules agree on policy, not yet on timing.

Not built here, each owned by the mechanism it needs: inheritance and supervision cost (need mortal owners and
overseers), landlords bidding for tenants after a plague (labour scarcity is in the wage, rent does not follow
it), elite overreach, confiscation and land reform (486, 542), tax farming (542), bondage on default
(`labour_bondage`). Dividends still split by ownership share; only land rent follows titles. The elite-share
range check under 4.2 needs a long baseline run: `python3 -m sim.tests --only agent_economy_wiring`'s
neighbours do not measure it, and no command does yet.

A state's debt to its named lenders (623) can be repaid in land once titles exist; the lender ledger is `Purses.named_lenders` (`sim/agents/named_lenders.py`).

## Finding (2026-10-21, from Complaint 662's capture)

In a Norse game in its sixth year a `hectare_land` market had one seller, no buyers, and a seller's floor about
273 orders of magnitude below its ask (`/tmp` capture, re-made by `sim/tests/test_staff_closure_reopening_scenario.py`'s
game and a wrapper around `unsold_search.clear_with_search`). A land seller's lowest acceptable price that close to
zero says the reservation it is built from (rent or yield over the rate) has collapsed. Measure where that floor
comes from before trusting land prices in that game.
