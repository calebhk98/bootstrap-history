# Every household can fall back on a plot it was never given

**Status:** partly done: own-plot growing is limited to land held or leased; a landless cohort leases land in the market and the lease checks its tools; open: a whole-game measurement of leasing, the team (draught animals, plant) check, and the own-plot growing itself reading the tool fallback hours

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

- Leasing in the market (Complaint 538 rules): `sim/economy/land_tenancy.py` (`match`, `rent_ask`, `lettable_hectares`)
  and `land_lease_year.lease_in_market`, called each year before the own-plot allocation. A cohort wants the hectares its
  floors need beyond what it works, no more than its hands and tools work; a holder lets what it holds beyond what it works
  for its own floors (a holder with no hands, a state, a firm or a lender lets all). The lease is a tenancy
  (`titles.lease`); `titles_worked.worked_share` and `Economy._hectares_held` read it, so the own-plot rule grows on leased
  land. Tests: `LeasingInTheMarketTests` in `sim/tests/test_economy_land_tenancy.py`, `sim/tests/test_economy_land_lease_year.py`.
- The tools check: `land_tenancy.hectares_workable` gives the hectares the cohort's hours work with the tools it holds
  (its stock, or what it rents: pass the rented stock with the held), counting the extra hours of the next tool and of
  working by hand (`tool_fallback.draws`), so a missing tool slows the work and does not stop it. Tests: `ToolsCheckTests`
  and `test_without_tools_the_same_hours_work_fewer_hectares`.

## Left

- The quick-tier economy fixture has no own-plot recipes (its cohorts grow nothing for themselves), so leasing is tested on
  built inputs and not in a stepped game; a stepped game with landless cohorts and a crop that needs a tool is not run.
- Tools are checked when the lease is sized. The own-plot growing itself (`households_own.own_production`) does not charge
  the by-hand hours of a short tool; a cohort that leases for the hands it has and then loses its tool works the same hours.
- Team (draught animals) and plant are not checked.
- Cohorts still differ in endowment only through titles and leases (landlessness is an outcome of the title seed,
  foreclosure and leasing, with no typed share); urban cohorts hold title through their ownership share like the rest.
