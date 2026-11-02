# State ownership map

Complaint 508 (closed) gave every fact of the engine one owner module: `sim/<module>/state.py` holds what a
module owns, `module_spec.py` the views it publishes and the commands it applies (`sim/ARCHITECTURE.md` section 3).
This map lists only the facts that still live in more than one place, which is where a change can miss a reader.
It lags the code: re-run each command before acting, and read the complaint named in a row for its status.

Commands run from the repository root. `X` is the filter `--include=*.py --exclude-dir=tests`. Counts are not
written here; `| wc -l` counts a listing.

| Fact | Where it lives | Two places? | Tracked by |
|---|---|---|---|
| Money balances | The shared `Book` (`sim/book.py`), held by the economy record; `Purses` (`sim/agents/purses.py`) adopts it (`adopt_book`). The ledger module (`sim/ledger/`) applies the seats' money commands | Writes outside the ledger's owners exist: `bash tools/done_check.sh` prints "book/ledger transfer calls outside owners" with the sites. The coin tally `home_coin_stock_units` (`sim/markets/port_world.py`) is separate from the book | none open |
| Goods balances | Seat tonnes by commodity key: `LedgerSeat._material_stock_ledger` (`sim/ledger/state.py`). Actors' and households' goods: units by good and tile in the economy book | Yes: two ledgers with different units and keys; nothing reconciles them | none open |
| Debt | One registry, `Contracts` (`sim/contracts.py`), shared by `Purses` and the economy record. Per seat, `FinanceSeat` (`sim/finance/state.py`) keeps bondage and arrears fields | The seat's fields are a smaller story beside the registry | `Complaints/closed/555` |
| People and employment | Three records: `DemographyWorld.pop_*` (`sim/demography/state.py`, all ages), `economy.record.workforce` (the labour core's `MarketState`: working people by labour area, trade and ability), and `WorkforceSeat.employees` plus slaves and freedmen (`sim/workforce/state.py`, `sim/labour/staff_book.py`) | Yes, by construction (all ages against working ones, the core against the staff books); the army and the levy are a fourth place | `Complaints/964`, `556`, `963` |
| Land and deposits | `LandWorld.tile_owners` (sovereignty, `sim/land/`) and the economy's `record.titles` and `tenancies` (rent rights, `sim/economy/titles.py`); deposits in `sim/world/deposits.py` and `sim/resources/` | Two maps with different meanings of "owner" | `Complaints/538` |
| Ways and works | `LandWorld.improvements`, `ways_under_construction`, `works`, `works_under_construction` | No | none |
| Plants and capacity | The economy's `record.producers`; the seat's `VenturesSeat.businesses` and plants (`sim/ventures/state.py`); actors' concerns (`sim/agents/`) | Yes: two implementations of running a business | `Complaints/514`, `510` |
| Orders and market outcomes | The economy's order book and record (`record.volumes`, `unsold`, `unmet`, `memory.prices`); the markets module's static commodity book (`MarketsWorld.market_book`, `market_flows`, `sim/markets/clearing.py`, `sim/world/market.py`) | Yes. `market_state` takes sold, unsold and unmet from the economy's record (`agent_market_record`) once the economy has opened; capacity, stock, floor and ceiling fields still come from the static book | `Complaints/507`, `ONE_PRICE_OWNER_PLAN.md` stage 6 |
| Prices | The economy's cleared prices (`memory.prices`, `sim/economy/prices_at.py`); the calculator's cost tables (`sim/prices/`); a national price rule and a legacy analytic model beside them | Yes | `Complaints/507`, `964` |
| Knowledge | `KnowledgeSeat.done` per seat (`sim/knowledge/state.py`); actors hold their own | Techniques in use are read from the ventures plants and actors' concerns | `Complaints/514` |
| Indicators | Derived yearly figures kept in state and read by screens and by wage and coin rules; owner none | A stale one is a year behind | `Complaints/554` |

## Commands that list a fact's writers and readers

Money:

    grep -rnE "purses\.(transfer|set_net|cover|write_off|pay_interest|pay_arrears|repay_from_purse)\(" sim X
    grep -rnE "book\.(post|transfer|settle)\(" sim X
    grep -rn "def pay_edge\|def receive_from_edge" sim

Goods: `grep -rnE "_material_stock_ledger" sim X` (seat tonnes); `grep -rnE "move_goods|settle_agent_takings|settle_goods" sim X`
(economy book); `grep -rnE "account_holdings" sim X`.

People: `grep -rnE "record\.workforce|agent_people_by_trade|people_in\(" sim X`; `grep -rnE "pop_working_age *=" sim X`.

Land: `grep -rnE "transfer_tile|tile_owners\.seed" sim X`; `grep -rnE "titles\.(seed|move|foreclose)" sim X`;
`grep -rnE "tile_owner_map|tile_owners" sim X`.

Plants: `grep -rnE "record\.producers\[" sim X`; `grep -rnE "works_under_construction" sim X`.

Market outcomes: `grep -rnE "market_flows|market_book|_market_entry\(" sim X`;
`grep -rnE "note_sale|note_purchase" sim X` (the only outside writers of the economy's staged orders);
`grep -rnE "market_state\(" sim X`; `grep -rnE "record\.(volumes|unsold|unmet|curves)|market_record\(|traded_volumes\(" sim X`.

Whether the economy's record and the static book still disagree for a good: `python3 -m sim.tests --only market_state_record_wiring`
(slow; it opens a game).

Indicators: `grep -rnE "output_per_head|wage_market_ratios|coin_metal_ratios|agent_baseline_prices|yearly_record" sim X`.

## What is left of 507 stage 6

- The founder's sales terms (`displaced_by_founder_tonnes`, `founder_sales_tonnes`) still come from the static book:
  the economy has no within-year counterfactual of the founder's sale. Either the economy clears the staged
  sales as an extra offer and reports the other sellers' change, or `displaced_producers` is redefined on the
  economy's unsold figure. Decide before deleting the founder-sales terms of `sim/world/market.py`.
- Then the static book (`market_outcome`, `market_conditions` in `sim/markets/clearing.py`, `sim/markets/demand.py`)
  can go for home goods; partner books keep `sim/world/market.py`.
