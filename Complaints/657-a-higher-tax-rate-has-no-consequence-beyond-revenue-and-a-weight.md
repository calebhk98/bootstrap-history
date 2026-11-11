# A higher tax rate has no consequence beyond revenue and a typed burden weight

**Status:** partly - a harvest tax and a land tax reach the farmer's and the owner's own rules; concealment of income from a form follows the rate and the officials' reach in both layers (actors and the economy's money, harvest and trade forms), and the AI state's rate-raise yield counts it; the flight comparison, the liability rule and the amnesty, immunity and remission levers are rules, fed by the engine into the labour market's year inputs (tenants flee, fugitives are kept and return) and into the AI state's menu, which nets the base lost to flight; unrest is built (`sim/agents/unrest.py`, read by `sim/campaigns/stability.py`) but the AI state's menu does not foresee it, so `FISCAL_BURDEN_WEIGHT` stays

Follows from 626 (tax rates as a state choice).

**What is wrong now.** A state can raise the rate of a form (a player's lever, or an AI state's `raise_rate` response). The
base responds in the ways listed under Built below (hiding, flight, liability), but not in these:

- Unrest from a heavy burden is built (`sim/agents/unrest.py`; `sim/campaigns/stability.py` reads `tax_burden.harvest_share_taken`
  and the liability burden), but nothing in the AI state's menu (`fiscal_response.py`, `fiscal_flight.py`, `government_fiscal.py`)
  foresees it.
- The producers' land demand and run decisions in the economy do not net a harvest tax off expected revenue
  (`land_market.demands_of`), and the farm-hours choice has no tax input.
- The AI state's `raise_rate` option does not count the base lost through unrest (it does net hiding and flight). It weighs a
  raise by `FISCAL_BURDEN_WEIGHT` (`sim/agents/tuning_fiscal.py`), a labelled stand-in; it retires when the menu values unrest too.

**Why it matters.** Without a full response of the base there is a ceiling to taxation only at the rate cap, and a state
cannot lose by overtaxing in every way a real one does (CLAUDE.md 4.1: the outcome should come from lower-level state, not
from a typed elasticity).

**What it would take.** Finish the payers' own choices (households and firms compare what they keep with what they could keep
elsewhere), then the AI state values the loss of base as a consequence of a raise. Test: raising a rate on a base whose payers
can leave lowers the base next year; an AI state with the loss in its menu raises a rate less than one without.

## Built

- **Harvest tax and farm effort.** `sim/agents/tax_burden.py` `harvest_share_taken` reads the state's present rates
  (levers included), the tiles each form covers and the share its officials reach. Its only reader is
  `sim/campaigns/stability.py`: the farm-hands leg (the labour package's farm allocation and `farm_intake`) is deleted, so
  nothing yet takes the harvest tax into a household's choice of farm hours against the wage; that choice belongs to the
  economy's plots and farm producers and is open.
- **Land tax reaches the owner's holding.** `tax_burden.land_tax_share_of_rent` turns a form on `land_rent` or `land_value`
  into a share of the rent; `YearInputs.land_tax_share_of_rent` carries it to `land_market.settle_year` and
  `titles.settle_tenancies`: a lessor whose managing cost plus the tax exceed the rent lets the title go (`titles.release`, 538).
- **Poll tax** acts through household cash: `taxes._collect_money` pays no more than the purse holds, and an unpaid remainder
  is an arrear.
- **Income is hidden from a rising rate.** `sim/agents/evasion.py` `hidden_share`: a payer hides the share at which the last
  unit's saving equals the rising cost of hiding it, up to a ceiling, so a higher rate hides more and a state whose
  officials reach more is hidden from less. `revenue.taxed_actors` assesses only declared income; `fiscal_response.rate_raise_yield`
  nets the extra hiding. The economy's forms hide by the same rule through `EconomySetup.hiding`
  (`sim/markets/port_setup.py`), so the economy imports nothing from the actors. Customs duties on border imports
  are not under it. `HIDEABLE_SHARE_OF_INCOME` and `HIDING_MARGINAL_COST_AT_CEILING` (`sim/agents/tuning_evasion.py`) are
  labelled heuristics with `retire` 657.
- Tests: `test_tax_evasion.py`, `test_tax_evasion_economy.py`, `test_tax_flight_and_liability.py`.

- **Flight is the migration rule.** `sim/labour/market/migration.py` scores each route by the income kept after the state's take
  in that area (`YearInputs.taxed_share`) less the move's cost, which now includes the expected penalty of recapture
  (`Route.expected_penalty`, from `sim/agents/flight.py` `expected_penalty_of_leaving`: the chance of recapture at the
  state's reach on the tile he goes to times what he owes with the penalty at that reach). Taxed land a fleeing tenant leaves
  is released to no holder by `sim/economy/titles_flight.py` `tenant_flees` (538's rule).
- **Liability is a state choice.** `sim/agents/liability.py`: individual, or collective per unit, where the stayers split the
  unit's assessment (the merismos). Tested for the sourced spiral: under collective liability a shock raises the stayers'
  take and a larger share leaves each year; under individual liability the take and the share leaving stay flat.
- **Levers** (`sim/agents/government_levers_tax.py`, through `lever`/`levers`): `liability`, `amnesty` (share of arrears
  waived), `immunity` (years a taker of deserted land owes nothing; `flight.share_after_immunity`) and `remission` (every
  form's rate, read through `government_levers.revenue_forms`, so revenue and `tax_burden` see it).
- **Hiding and Yitzhaki.** A penalty in proportion to the tax unpaid leaves the rate out of the choice; the rate effect in
  `evasion.py` comes only from the hiding-cost curve, which stays labelled (`HIDING_MARGINAL_COST_AT_CEILING`).
- Tests: `test_tax_flight_and_liability.py`.

- **Flight is wired into the year.** `YearInputs.taxed_share_by_tile`, `state_reach_by_tile`, `amnesty_share` and `immunity_years` are filled
  by `sim/markets/port_flight.py` from `sim/agents/flight_inputs.py` (the state's income forms times its reach on the tile, under its liability rule
  with the people who fled counted out of those who remain). `sim/economy/flight_routes.py` turns them into `YearInputs.taxed_share` and each route's
  `expected_penalty` (the actors' `flight.expected_penalty_of_leaving`, handed in as `EconomySetup.flight`, so the economy imports no actor). After the
  labour year `sim/economy/flight_step.py` runs `flight_year.py`: tenants of an area people left leave their land (`titles_flight.tenant_flees`), the leavers
  are kept as `EconomyRecord.fugitives` with what they owe, and a fugitive returns by the migration rule run backwards (his refuge's income against home's after the take,
  less the arrears, `flight.arrears_owed_by_fugitive`, with the amnesty lever; `flight.share_after_immunity` on the take he meets at home).
- **The AI state's menu counts flight and has the tax-response levers.** `fiscal_flight.py` calls the migration rule for the share of payers who leave at a take
  (only those who can reach a tile the officials do not); `rate_raise_yield` nets the base lost that way on forms on income. The menu offers `remission`
  (only where a cut yields more), `amnesty` (where people have fled) and `liability` (collective, where the leavers' assessment on the stayers recovers more than the extra flight loses),
  and `Government.pull_tax_response_levers` sets the levers the choice covered money with.
- Tests: `test_tax_flight_wiring.py` (rules called with built inputs; the engine's year is covered only by the whole-game smoke topics).

**`FISCAL_BURDEN_WEIGHT` stays.** The menu now nets flight for a rate raise, but (1) unrest (built, `sim/agents/unrest.py`) is the other loss it stood in for and the menu does not foresee it;
(2) the levy and the demand in kind, which also carry `income_taken`, do not net flight; (3) with the migration rule's cap on the share who consider
moving in a year, flight alone never makes a raise yield less in any rate or reach tried, so the loss the weight stands for is not all flight.

**Still open.** (a) Immunity is read only where a fugitive weighs returning to deserted land: released land is still never taken up by anyone else (nothing in the economy
fills a title below one on a tile except a clearer's new ground), so a taker's years without tax are not applied after the first comparison. All net outflow from a taxed area is
treated as flight (no split of the part that is not about tax); a fugitive's refuge is the area that gained most that year, not tracked per person; arrears accrue as a year's take at
the area's subsistence, not the person's income, and `Route.expected_penalty` counts this year's take only (the fugitives' arrears are not added to a new leaver's). Whole-game effect not
measured (a slow topic and the fingerprint are needed). (b) `remission` is never offered in the cases tried (see above). (d) The AI state's menu does not foresee unrest. (e) The hiding-cost curve has no source.

## Research needed

No source on pre-modern tax pressure, flight and abandonment was opened, so the hiding constants and `FISCAL_BURDEN_WEIGHT`
have none. The question: how did taxpayers respond to a heavier take in the Roman and medieval worlds, by form (flight of
tenants and the abandoned land of the late empire, anachoresis in Roman Egypt, concealment, evasion, revolt), and at what
share of the harvest did each begin? Sources to open: Roman Egypt tax-flight papyri studies, the Codex Theodosianus on agri
deserti, and medieval English peasant flight and tallage studies. A response curve fitted to those is a validation of the
mechanism, not an input to it.
