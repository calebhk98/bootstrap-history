# Every household can fall back on a plot it was never given

**Status:** closed - own-plot growing is limited to land held or leased; landless cohorts lease and the tools, team and plant a cohort holds set the hours its plot takes (by hand when short); a stepped fixture economy tests it

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
- `titles_worked.py`: `worked_share` (title less what is let out, plus what is worked as a tenant) and `allocate_hectares` (claims cut by one factor when they exceed the tile arable land). `Economy.hectares_held` (`sim/economy/economy.py`, delegating to `titles_plots.py`) decides the allocation before any growing.
- Tests: `LandHeldTests` in `sim/tests/test_economy_households_own.py`.

- Leasing in the market (Complaint 538 rules): `sim/economy/land_tenancy.py` (`match`, `rent_ask`, `lettable_hectares`)
  and `land_lease_year.lease_in_market`, called each year before the own-plot allocation. A cohort wants the hectares its
  floors need beyond what it works, no more than its hands and tools work; a holder lets what it holds beyond what it works
  for its own floors (a holder with no hands, a state, a firm or a lender lets all). The lease is a tenancy
  (`titles.lease`); `titles_worked.worked_share` and `Economy.hectares_held` read it, so the own-plot rule grows on leased
  land. Tests: `LeasingInTheMarketTests` in `sim/tests/test_economy_land_tenancy.py`, `sim/tests/test_economy_land_lease_year.py`.
- The tools check: `land_tenancy.hectares_workable` gives the hectares the cohort's hours work with the tools it holds
  (its stock, or what it rents: pass the rented stock with the held), counting the extra hours of the next tool and of
  working by hand (`tool_fallback.draws`), so a missing tool slows the work and does not stop it. Tests: `ToolsCheckTests`
  and `test_without_tools_the_same_hours_work_fewer_hectares`.

- Tools, team and plant in the growing itself: `sim/economy/plot_means.py` (`hours_for_runs`, `runs_within`) gives the hours
  runs take with the stock held: a short tool is drawn from by the next tool then by hand (`tool_fallback.draws`), and runs
  beyond the plant held (a draught team, a plough) are worked by hand at the recipe's by-hand hours factor (1.0 where the
  recipe states none). `households_own.own_production` and `hours_for_own_plan` take `held_goods`; `Economy._grow_own` and
  `_fixed_home_hours` read each cohort's stock; lease sizing (`land_tenancy.hectares_workable`) uses the same function.
  Tests: `sim/tests/test_economy_plot_means.py`.
- Stepped fixture: `fixture_setups.plot_tool_setup` (own-plot recipe needing a hoe, nobody holds one) with every title given to a
  landlord; `sim/tests/test_economy_own_plot_leasing_smoke.py` (SMOKE, slow tier) asserts each landless cohort leases, works
  hectares and grows its floor.

## By design

- Cohorts differ in endowment only through titles and leases. Landlessness is an outcome of the title seed, foreclosure and
  leasing, with no typed share of landless households: a typed share would be a hardcoded outcome (CLAUDE.md 4.1). Urban
  cohorts hold title through their ownership share like the rest.
- Not wired: the opening's own-plot growing (`opening_own.py`) and the plot-hours schedule (`household_hours_year.usable_plot_hours`)
  still take the means as held; they size a stationary opening, not a year's work.
