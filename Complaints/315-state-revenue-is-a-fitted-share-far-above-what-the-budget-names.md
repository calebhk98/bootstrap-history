# State revenue is a fitted share of labour value, several times what the modelled budget spends

**Status:** partly - revenue is the declared forms assessed on modelled bases, in coin or in kind (test state_revenue_forms); a form can fall on the strata's earned income (`stratum_income`, test state_strata_fiscal), on the rent producers paid for land let (`land_rent`) or on land's capital value, that rent over the market rate (`land_value`) (test state_land_revenue); Rome keeps its land tax as the harvest form only: a `tributum_soli` on land value was added and taken out again (2026-10-09), because the provincial tribute was one tax, collected as a share of the crop in some provinces (Sicily's tenth) and as a share of assessed property in others (Syria's one per cent, Appian, Syrian Wars 50), so stacking both empire-wide counts it twice; splitting Rome's land tax by province is open. Remaining: the rent is drawn from the edge, not from named owners, because the agent economy keeps rent with household cohorts and strata are rank slices of them (a world that can name owners returns them from `land_rent_owners()` and the tax is then taken from their purses); no civilisation declares a stratum-income form (no source gives one); the surplus is spent on unnamed works rather than lines with their own stock (see "Lines the budget lacks")

`SimWorld.state_revenue` is the working people not under arms, at the unskilled wage, times the economy's output factor, times `starting_tax_share` times state capacity. With the standing lines of 300 built (army, officials, roads, public buildings, court, dole, navy), a healthy Rome spends about a third of that and Han about a sixth, so neither goes short until a plague, a collapse of output or a threat-driven army takes the revenue below need. Measure: `python3 sim/budget_series.py rome_100ad 200 1` (script since removed; recover with `git show 97473f1:sim/budget_series.py`) and the same for `han_china_100ad`; the table shows revenue beside the need by line. With `BUDGET_SERIES_IDLE_FOUNDER=1`, Rome goes short from the third-century crisis on and Han never does; Norse runs close to balance from the start.

Two ways to close it, and the second is the honest one. Spending that the budget does not name (campaigns beyond the standing force, building beyond upkeep, gifts to the army, tax collection itself) has no line of its own: a reserve above `RESERVE_CEILING_YEARS_OF_NEED` now hires public works and is lent through the capital market (`government_surplus.py`, 327, 307); each unnamed purpose still wants a physical basis. Revenue itself is a share of labour value at one wage, not of a taxable surplus (rent, trade, the harvest after subsistence); it should follow what can be collected.

All the new line sizes (`tuning_spending.py`) are labelled heuristics, so the ratios above move with them; do not treat the ratios as findings about Rome or Han.

Related: 287, 314.

Owner decision (2026-10-02): should be fixed from actual values: a state can have several revenue forms (land, wealth, trade on imports and exports, people), often paid in kind (a share of food), not only coin.

Built (owner decision 2026-10-02): each civilisation declares `state_revenue` forms (basis, rate, optional `paid_in`, source) in its file; `sim/agents/revenue.py` assesses them on bases in `revenue_bases.py` (harvest, adult labour years, imports, exports, coin stock); in-kind revenue enters the state's stores and is used by its lines or sold through the goods market (`government_stores.py`). `starting_tax_share` no longer sets state revenue. Open: most rates are labelled placeholders (confidence D in the data); the surplus against the named lines persists (`python3 sim/budget_series.py rome_100ad 100 1`); the grain valuation follows the goods market's spot quote, which swings in some runs, so land tax in coin's worth swings with it (same command, Han).

Update (strata): `basis: "stratum_income"` (`revenue_bases.py`) is the earned income (`edge:` purposes of `record.income`) of the home country's strata since the state last assessed it, optionally limited to named strata (`from_strata`). It is collected from the payers' purses by `ledger.transfer` (never more than a purse holds), so the money is the strata's loss and the state's gain, not created at the edge. The world answers `country_strata()` (`sim/engine/agents_port_budget.py`). To use it a civilisation's `state_revenue` adds a form such as `{"form": "income_tax", "basis": "stratum_income", "from_strata": ["rich"], "rate": <rate>}` with a sourced rate (a property tax on the rich stratum stands in for rent). Measured with a scratch driver (a Rome start, `agent_economy` off, `game.advance_actors(year)` six years, the home government's `record.income` and `record.outlays` differenced each year): before, year 1 revenue 5.4e9 against spending 2.2e9 (surplus 3.2e9), year 2 surplus 1.3e9, then works (the unnamed sink, capped at a tenth of the working age) took the rest, 3.2e9 of 5.5e9 spent from year 3 and the surplus fell to nil; after: the same first two years, then relief to the poor stratum (0.5e9 in alternate years, its reported unmet food and housing) and works; with a form `{basis: stratum_income, rate: 0.01}` added to the civilisation's forms, revenue rises from 5.5e9 to 6.9e9 from year 3 (the strata earn about 4e11 a year at home), collected from the strata's purses by `ledger.transfer`.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 286 (`closed/286-state-budget-models-only-army-and-officials.md`): the state budget names only army and officials; surplus should be spent on named lines with a stock of works (roads, aqueducts) and their upkeep.
- 105 (`closed/105-add-a-state-fiscal-budget-model.md`): state fiscal budget: the remaining pieces are 286 (above) and the revenue forms in this issue.

## Update (land bases, 2026-10)

`land_rent` and `land_value` (`revenue_bases.py`) read `economy.api.land_rent_paid_by_tile` (`sim/economy/land_rents.py`): each tile's rent per hectare times the hectare-years its producers worked last year, in coin. `land_value` divides by `market_rate()` and is nil without a rate. Not every civilisation had a land tax beyond the harvest forms it already declares: Han, Mexica and Norse take theirs from the harvest, England in 1300 had customs and a movables subsidy but no standing land tax, so only Rome gained a form. No stratum-income form was added because no source names a rate. The Rome form is measured only on fixtures (a whole game was not built); its yield in a played start is unmeasured.

### Lines the budget lacks

The standing lines are army, officials, roads, public buildings, court, dole and navy (`budget.standing_lines`). Surplus beyond the reserve relieves reported hunger, then hires works. Named lines still missing, each with what it needs:

- Fortifications and garrison works: a stock of wall length per tile held, from the frontier and the sack hazards, with upkeep as masons; needs a wall stock on the tile record.
- Water and drainage (aqueducts, canals, irrigation): a stock per town and per irrigated tile, upkeep as masons and labour; needs the water works to be tile state, not only a node.
- Granaries and relief stocks: a grain reserve held in the state's stores against bad harvests, bought when the price is low; needs a target in years of need and a store-keeping loss.
- Tax collection: collectors as a share of the revenue each form raises, by form (a customs post per trade crossing, assessors per land form); needs a cost per unit of base per form.
- Campaigns beyond the standing force: marching and supply as a function of the threat and distance, paid from stores and coin; needs the army to move on the map.
- Public works for the capital and temples: building to a stock of floor area beyond upkeep; needs the stock and a motive other than surplus.
- Gifts and donatives to the army and officials: a per-head payment tied to accession or crisis events; needs those events as state (the events agent's area).
None is built here.
