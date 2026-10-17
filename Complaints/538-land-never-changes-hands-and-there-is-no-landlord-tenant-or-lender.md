# Land never changes hands, and there is no landlord, tenant or lender

**Status:** open

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
