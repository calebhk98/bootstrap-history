# A higher tax rate has no consequence beyond revenue and a typed burden weight

**Status:** partly - a harvest tax and a land tax reach the farmer's and the owner's own rules; concealment of income from a form on what actors hold now follows the rate and the officials' reach, and the AI state's rate-raise yield counts it; flight, unrest (486) and concealment under the harvest and trade forms are open, so `FISCAL_BURDEN_WEIGHT` stays

Follows from 626 (tax rates as a state choice).

**What is wrong.** A state can raise the rate of a form (a player's lever, or an AI state's `raise_rate` response), and the
form yields more of the same base. Nothing else follows from the higher rate: the taxed base does not shrink, hide, move
or stop being worked, and compliance does not wear down. The AI state weighs a raise only by `FISCAL_BURDEN_WEIGHT`
(`sim/agents/tuning_fiscal.py`), a typed heuristic, so it will keep raising a rate as far as the shortfall asks, up to the
yearly step. A rate that costs nothing but a weight is still an input, not an outcome.

**Evidence.** `sim/agents/fiscal_response.py` (`menu`, the `raise_rate` option); `sim/agents/revenue.py` (the base does not
read the rate); `concealed` and `defiance` on `ActorRecord` are set by demand answers, not by the rate.

**Why it matters.** Without a response of the base, there is no ceiling to taxation but the rate cap, and no way a state
loses by overtaxing (CLAUDE.md 4.1: the outcome should come from lower-level state, not from a typed elasticity).

**What it would take.** A mechanism for how taxpayers respond to the share taken: concealment of income and land,
migration out of a taxed tile, withdrawal of labour, from the payers' own choices (households and firms compare what they
keep with what they could keep elsewhere), not a typed elasticity. Then the AI state values the loss of base as a consequence
of a raise, and `FISCAL_BURDEN_WEIGHT` retires.

**Test.** A test: raising a rate on a base whose payers can conceal or leave lowers the base next year; an AI state with the
loss in its menu raises a rate less than one without.

## Progress

- **Harvest tax reaches farm effort.** `sim/agents/tax_burden.py` `harvest_share_taken` reads the state's present rates (levers
  included), the tiles each form covers and the share its officials reach. `LabourWorld.harvest_share_taken`
  (`sim/engine/labour_port.py`) hands it to `_farm_hour_value_over_wage` (`sim/labour/labour_allocation.py`), which now
  decides on `farm_intake.value_over_wage_after_tax`: a farm hour's food at the staple's price less the share taken, over the
  wage. Hands leave the land by the existing `kept_farm_workers` rule when the ratio falls under one.
- **Land tax reaches the owner's holding.** `tax_burden.land_tax_share_of_rent` turns a form on `land_rent` (its rate) or
  `land_value` (its rate over the market rate of interest) into a share of the rent. `YearInputs.land_tax_share_of_rent`
  carries it to `land_market.settle_year` and `titles.settle_tenancies`: a lessor whose managing cost plus the tax exceed the
  rent holds a loss and lets the title go (abandonment through `titles.release`, the path 538 built). `tax_burden.after_tax_rent`
  is the owner's net figure.
- **Poll tax** already acts through household cash: `taxes._collect_money` pays no more than the purse holds, and an unpaid
  remainder is an arrear.
- Tests: `sim/tests/test_tax_pressure_reaches_decisions.py` (share taken, harvest tax lowers farm effort, land tax lowers the
  net rent and makes a marginal tenancy a loss). They call the rules with built inputs; the engine wiring (`labour_port`,
  `economy_port_land`) is covered only by whole-game topics.
- **Income is hidden from a rising rate.** `sim/agents/evasion.py` `hidden_share`: a payer hides the share at which the last
  unit's saving (the rate, less the chance of being found times the tax and a penalty scaled by the state's reach, the
  penalty rule of `demand_answer.py`) equals the rising cost of hiding it, up to a ceiling. So a higher rate hides more; a
  state whose officials reach more of the payers is hidden from less; full reach hides nothing.
  `revenue.taxed_actors` (forms on `stratum_income`, `land_rent`, `land_value`) assesses only the declared income; `Assessment.concealed`
  records the rest. `fiscal_response.rate_raise_yield` is the menu's yield of a full rate step net of the extra hiding it
  provokes (`raise_coin_rates` uses the same figure), which also corrects the old worth that took the whole base as the yield
  of a raise (it ignored the rate). Hidden income stays with the payer, so household disposable income and saving follow the
  existing purse rules. The cost of hiding is an expected cost in the choice, not a cash flow.
  Constants `HIDEABLE_SHARE_OF_INCOME`, `HIDING_MARGINAL_COST_AT_CEILING` (`sim/agents/tuning_evasion.py`) are labelled heuristics
  with `retire` 657; no source found. Tests: `sim/tests/test_tax_evasion.py`.
- Still open: flight from a taxed tile and withdrawal of labour (a stronger form of the above, for households' choice of
  place); hiding under the harvest and trade forms; the economy layer's money forms (`sim/economy/taxes.py`) still evade only
  by the state's capacity; no unrest or flight (486); the producers' land demand and run decisions in the economy do not net a harvest
  tax off expected revenue (`land_market.demands_of`); the AI state's `raise_rate` option does not yet count the base lost
  through these. `FISCAL_BURDEN_WEIGHT` therefore stays as the labelled stand-in (the menu now counts the lost yield but not the
  flight or unrest); it retires when the menu values those too.
- Sources: no source on pre-modern tax pressure and abandonment (agri deserti) was opened in this session, so none is cited.
