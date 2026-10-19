# State ownership map

For each fact in Complaint 508's ownership table: who owns it today (if anyone), who writes it, who reads it,
its units, when in the year it changes, and whether a second place computes it. Counts are not written here;
each command lists the sites, and `| wc -l` counts them. Re-run before acting: this map lags the code.

All commands run from the repository root. `X` below is the shared filter
`--include=*.py --exclude-dir=tests`. Where a fact has no single owner, the row says so and names the pair.

## Summary

| Fact (508) | Owner today | Two places hold or compute it? |
|---|---|---|
| Money balances | The shared `Book` (`sim/book.py`), held by the economy record; `Purses` adopts it | No for the balances. Yes for the founder's coin counts: `home_coin_stock_units` is a separate tally |
| Goods balances | None | Yes: the founder's `_material_stock_ledger` (tonnes by commodity) and the economy book's holdings (units by good and tile) |
| Debt | The shared `Contracts` registry, adopted by `Purses` | Mostly no; the household also keeps `bondage_debt` and freeze fields of its own |
| People, skills, employment | None | Yes: `sim.population` (all ages), `record.workforce` (working people by area, trade, ability), `household.employees` (the founder's staff) |
| Land and deposits | Partial: `record.titles` for rent rights, `state.economy.tile_owners` for sovereignty | Two ownership maps with different meanings; deposits live in `sim/world` apart from both |
| Transport assets | `state.economy.improvements` and `ways_under_construction`, read by geography | No |
| Plants and capacity | None | Yes: `record.producers` (economy), `projects.operating` and actor `concerns` (engine), `economy.works` (construction); Complaint 514 |
| Orders and market outcomes | None | Yes: the engine's static commodity book and flows, and the economy's order book and record. This slice narrows it |
| Knowledge and objectives | `projects.done` per seat; actors hold their own | Not measured here |
| Indicators | None | Several yearly figures are computed in the engine and read back by screens |

## Money balances

- Owner: `Book` in `sim/book.py`. `Purses` (`sim/agents/purses.py`) calls `adopt_book`, so actors' purses and the
  economy's markets share one book. `HouseholdState.capital` is a property over the purse (not a duplicate).
- Writers: `grep -rnE "\.purses\.(transfer|set_net|cover|write_off|pay_interest|pay_arrears|repay_from_purse)\(" sim X`
  and `grep -rnE "book\.(post|transfer|settle)\(" sim X`; the founder and seats go through `pay_edge` and
  `receive_from_edge` (`grep -rn "def pay_edge\|def receive_from_edge" sim`).
- Readers: `grep -rnE "purses\.(purse|net|debt|deposit)\(|account_balance" sim X`.
- Units: coin in the actors' currency (`COIN` in `purses.py`) and the economy's own currency per area, joined by
  `EDGE_EXCHANGE`. Timing: postings as they happen all year; the economy's flows settle at the year's close.
- Second computation: `home_coin_stock_units` (`sim/engine/foreign_payments.py`) tallies the society's coin
  separately from the book (it feeds the price level).

## Goods balances

- Owner: none. The founder (and each seat) holds `holdings._material_stock_ledger`, a counter of tonnes by
  commodity key (`sim/engine/economy_materials.py`). Actors and cohorts hold goods in the economy book, in units
  by good and tile.
- Writers: `grep -rnE "_material_stock\(\)\[|_material_stock_ledger" sim X` (founder);
  `grep -rnE "move_goods|settle_agent_takings|settle_goods" sim X` (economy book).
- Readers: `grep -rnE "material_stock_t\(" sim X`; `grep -rnE "account_holdings" sim X`.
- Units: tonnes against units (`tonnes_per_unit` in `sim/engine/material_units.py` converts). Timing: the founder's
  ledger moves at each order; `_material_opening_stock` snapshots it for the year's accounting; the economy book
  moves in the year's clearing.
- Two places: yes, two ledgers with different units and keys. `SeatParty._move_stock` (`goods_market_api.py`)
  writes the founder's; nothing reconciles it with the book's holdings.

## Debt

- Owner: `Contracts` (`sim/contracts.py`), one registry shared by `Purses` and the economy record (`adopt_book`).
  Complaint 555 is its owner's package.
- Writers: `grep -rnE "contracts\.(add|open|draw|repay|adopt|write_off|close)" sim X`; credit clearing in
  `sim/economy/credit.py`, called from `sim/economy/economy.py`.
- Readers: `grep -rnE "credit_room|exposure|lent_by_borrower|\.debt\(" sim X`.
- Units: coin, with a rate per year. Timing: requests are made at one year's close and cleared at the next lending.
- Second place: the household's own fields (`grep -rnE "bondage_debt|credit_frozen_until|insolvent_years" sim X`)
  are a second, smaller debt story outside the registry.

## People, skills, employment

- Owner: none. Three records: `sim.population` (demography; saved as the `pop_*` fields of `PopulationState`),
  `economy.record.workforce` (the labour core's `MarketState`, working people by labour area, trade and ability),
  and `household.employees` (the founder's own staff, trade to head count).
- Writers: `grep -rnE "household\.employees\[" sim X`; `grep -rnE "pop_working_age *=" sim X`;
  the workforce is written inside `sim/labour/` and `sim/economy/labour_state.py`.
- Readers: `grep -rnE "household\.employees" sim X`; `grep -rnE "\.population\.(total|working_age)" sim X`;
  `grep -rnE "record\.workforce|agent_people_by_trade|people_in\(" sim X`.
- Units: heads (workforce counts the working share; population counts all ages), hours for labour. Timing:
  demography turns over at the year's step; the labour core clears each year inside the economy's year.
- Two places: yes. Compare `sim.population.total` with the sum of
  `economy.agent_people_by_trade()` on an opened game: they differ by construction (all ages against working ones), so any screen
  that mixes them needs to say which it means.

## Land, deposits, transport assets

- Owners: `economy.record.titles` and `tenancies` (rent rights, `sim/economy/titles.py`) and
  `state.economy.tile_owners` (sovereignty and control, `sim/engine/tile_ownership.py`). Different facts that share
  the word owner. Deposits are modelled in `sim/world/deposits.py` and the engine's `mine_deposits.py`, with no owner
  object. Roads, ports and canals: `state.economy.improvements` and `ways_under_construction` (`sim/engine/ways.py`),
  read by `sim/geography`.
- Writers: `grep -rnE "transfer_tile|tile_owners\.seed" sim X`; `grep -rnE "titles\.(seed|move|foreclose)" sim X`;
  `grep -rnE "improvements\[" sim/engine X`.
- Readers: `grep -rnE "tile_owner_map|tile_owners" sim X`; `grep -rnE "record\.titles" sim X`;
  `grep -rnE "deposit" sim/world sim/engine -l`.
- Units: shares of a tile (titles), tile ids (owners), hectares and rent per hectare-year. Timing: rent flows in the
  year's clearing; titles move at foreclosure; owners change at conquest or transfer.
- Two places: a tile's holder and its sovereign can be read from different maps; check which a caller wants.

## Plants and capacity

- Owner: none yet (Complaints 510 and 514, `FIRMS_OWN_PLANTS_PLAN.md`). Economy producers: `record.producers`.
  The engine's view of what runs: `projects.operating`, `actor.concerns`, and `economy.works` for construction.
- Writers: `grep -rnE "projects\.operating\.(add|discard|remove)" sim X`; `grep -rnE "record\.producers\[" sim X`;
  `grep -rnE "works_under_construction" sim X`.
- Readers: `grep -rnE "projects\.operating" sim X`; `grep -rnE "record\.producers" sim X`;
  `grep -rnE "\.concerns\b" sim X`.
- Units: runs of capacity a year (producers), a technique id (engine), a capacity figure per tile (works).
  Timing: producers enter and exit at the year's close; the engine's operating set changes at project completion
  and closure.
- Two places: yes; this is what 514 consolidates.

## Orders and market outcomes

- Owner today: split. The agent economy owns the clearing and its record (`economy.record.volumes`, `unsold`,
  `unmet`, `memory.prices`, `curves`); the engine owns a second, static clearing: the commodity book
  (`state.economy.market_book`), the year's flows (`market_flows`) and `market_clearing._market_outcome`.
- Writers: economy: `sim/economy/year_goods.py` (the record) and, from outside, only `agent.note_sale` and
  `note_purchase` for staged orders (`grep -rnE "note_sale|note_purchase" sim X`). Engine:
  `grep -rnE "market_flows|market_book|_market_entry\(" sim X` (guarded by `test_market_records_ownership.py`).
  The economy's record is guarded by `test_economy_market_record_walls.py`.
- Readers: `grep -rnE "market_state\(" sim X`; `grep -rnE "record\.(volumes|unsold|unmet|curves)|market_record\(|traded_volumes\(" sim X`;
  `grep -rnE "_material_prices\(\)" sim X`.
- Units: the record is in the good's units; `market_state` reports tonnes (the port converts). Timing: the engine's
  flows accrue through the year and enter its clearing when it closes; the economy's record is the last closed year.
- Two places: yes, and measured: `python3 -m sim.tests --slow --only market_state_is_economy_record`. Before this
  slice `market_state` read the engine's book for sold, unsold and unmet, and the two disagreed for most goods.

### The slice done on this branch

`market_state` (`sim/engine/market_clearing.py`) now takes `society_sales_tonnes`, `unsold_tonnes` and
`unmet_demand_tonnes` from the economy's record, through `EconomyPort.agent_market_record`. The record gained
`unsold` and `unmet` beside `volumes` (`sim/economy/record.py`, `year_goods.py`, `api.market_record`). The screen
reads that feed `tithable_sales_value` and `displaced_producers` follow it. The static book still answers while
the economy opens, and for a commodity with no priced material.

### What is left of 507 Stage 6

- `displaced_by_founder_tonnes` and `founder_sales_tonnes` still come from the static book: the economy has no
  within-year counterfactual of the founder's sale. Needs a design: either the economy clears the founder's
  staged sales as an extra offer and reports the other sellers' change, or `displaced_producers` is redefined on
  the economy's unsold figure. Decide before deleting `sim/world/market.py`'s founder-sales terms.
- `price_ratio`, capacity, stock and the floor and ceiling fields still come from the book; their readers are
  `grep -rnE "market_state\(" sim X` and the tests that name them.
- Then `_market_outcome`, `_market_conditions`, `market_demand.py` and the `MarketClearingMixin` entry in the `Sim`
  base list (`sim/engine/core.py`) can go for home goods; partner books keep `sim/world/market.py`.

## Knowledge and actor objectives

- Owner: `ProjectsState.done` per seat for the techniques the founder knows; actors hold their own knowledge and
  objectives (`sim/agents/`). Not measured further here.
- Writers: `grep -rnE "projects\.done\.(add|update|discard)" sim X`. Readers: `grep -rnE "projects\.done\b" sim X`
  (the most-read project field).
- Second place: techniques in use are read from `projects.operating` and actors' `concerns`; see Plants.

## Indicators

- Owner: none (Complaint 554 would be reporting). Yearly derived figures kept in state:
  `grep -rnE "output_per_head|wage_market_ratios|coin_metal_ratios|agent_baseline_prices|yearly_record" sim X`.
- They are written at the year's close (`_step_market`) from the economy's and the engine's figures, then read by
  screens and by wage and coin rules, so a stale one is a year behind. Units differ (ratios, per-head indices,
  prices); each declaration in `sim/engine/state.py` carries a comment saying what it is.
