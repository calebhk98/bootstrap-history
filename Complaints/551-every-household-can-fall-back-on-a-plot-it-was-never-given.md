# Every household can fall back on a plot it was never given

**Status:** open

Found by an outside reviewer reading the repository; checked against the code.

- `sim/economy/households_own.py` puts a cohort's unhired hours into land-only recipes on its own tile,
  up to its floors, and only then reports `plot_hectares` for the land market.
- `land_market.py` (`_clear_tile`) gives own plots first claim on the arable area, but when the plots
  exceed it the food already grown is not cut back.
- So every cohort, including the poorest and town dwellers, has a farming fallback. There are no
  landless labourers, tenants or urban households without one, and no team or tools are checked.
- Cohorts are income classes; their property income comes from `ownership_share`, which is the
  income distribution (538). Income does not say who owns land, workshops or plant.

## What it would take

- Allocate land, tools and labour before production; own-plot growing only for households holding
  land (owned or leased, 538) and the means to work it.
- Cohorts that differ by endowment (landholder, tenant, landless, urban) as well as income.
- Related: 538 (titles and tenancy), 545 (the opening ignores own-plot growing).
