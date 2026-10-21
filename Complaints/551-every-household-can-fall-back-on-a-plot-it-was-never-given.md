# Every household can fall back on a plot it was never given

**Status:** partly done: own-plot growing is limited to land held (titles, tenancies); leasing land in the market and the tools check remain open

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

## What was done

- `households_own.own_production` and `hours_for_own_plan` take the hectares the cohort holds: a cohort with none grows nothing and keeps back no hours; a holder grows no more than those hectares yield (`hours_on_land`).
- `titles_worked.py`: `worked_share` (title less what is let out, plus what is worked as a tenant) and `allocate_hectares` (claims cut by one factor when they exceed the tile arable land). `Economy._hectares_held` decides the allocation before any growing.
- Tests: `LandHeldTests` in `sim/tests/test_economy_households_own.py`.

## Left

- A landless cohort leasing land in the land market at the posted rent (a tenancy that is not a foreclosure) is not built.
- Tools and team are still not checked. Cohorts still differ only by income class; landlessness is an outcome of the title seed (ownership share) and of foreclosure, with no typed share.
