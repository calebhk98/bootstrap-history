# History of Complaint 649 (as it stood before it was trimmed)

Moved from the complaint file. Figures and line numbers here are as of the time they were written and may be stale; the complaint carries the current state.


Follow-up to Complaint 593 (the foreign state is now the one `Government`, scoped to its country; `sim/agents/country_state.py`).

**What is wrong.** The home `Government` reads the home-only engine; a country's `CountryWorld` now answers most of those
readings from its profile and its part of the one economy, but these have no per-country source yet:

- Unskilled people: `national_people("labourer")` is still the working age, as at home (labelled heuristic in `country_state.py`, with the fallback for a country the economy has no part for).
- Interest groups and patronage: `group_claims` is empty and `patron_ask` is zero abroad.
- Research: a country's state copies but does not originate research (`Government.researches`), as research hands are the founder's.

**Done.** A country's `material_cost` and `material_price` are its own market areas' quote (`CountryAnswers.price_per_tonne`,
nothing where they quote none); its `coin_regime` is the one economy's money standard and its `coin_stock_value` is the
backing metal in the money held on its tiles at its own price of that metal (`country_figures.money_held`). Checks:
`sim/tests/test_country_state.py`, `sim/tests/test_country_economy.py`.

A country's `trade_value` is its own trade book: the economy record keeps what the merchants carried by good and tile pair
(`record.carried_goods`, `sim/economy/carried_book.py`: tonnes, value at the origin's price, value at the destination's
price), and what crossed the country's border is valued as imports where they landed and exports where they left
(`country_figures.trade_book`, `CountryAnswers.trade_book` and `trade_value`). Its `national_people` for a skilled trade is the
people its labour markets hold in it (`CountryAnswers.people_of_trade`). The trade book counts the merchants' carried
goods only; the home state's `foreign_trade_by_year` (trade with off-map partners) has no country counterpart. Checks:
`sim/tests/test_carried_book.py`, `sim/tests/test_country_economy.py`, `sim/tests/test_country_state.py`.

A country's `equipment_kg_per_soldier` is the burden at the share of the military work its own state holds (its knowledge and
its civilisation's starting techs), read through `military_work_ids` and `equipment_kg_at_adoption`. Its `land_rent_owners` are its
own strata laid along its own cohorts' rent curve (`CountryAnswers.land_rent_curve`; nobody while its economy keeps no cohorts). Its
visible taxpayers include the playing seats of that country (`seat_taxpayers`); the home state's visible taxpayers use the same
selection for the home country, where a seat with no country is the game's own. Checks: `sim/tests/test_country_state.py`,
`sim/tests/test_country_economy.py`, `sim/tests/test_home_state_taxpayers.py`. A firm's country is the one its record names
(`ActorRecord.country`, none meaning the home country; `ActorRegistry.country_of`), the same field that picks its world scope; the home
state's visible taxpayers take firms by that rule (`firm_taxpayers(country)`, beside `seat_taxpayers`), and a country's state
selects its firms by the same field. A plant carries no tile and a firm one `location`, so a firm has one country: its taxable
income is not split by where its plants earn. Splitting it needs a tile on each plant and the country of that tile
(`setup.country_of`), which is a mechanism not built yet.

A plant's yearly books (`business_books.operate`) are read through `world.plant_books`: at home the founder's engine's figures
(`business_plant_books.home_books`); abroad the country's own: takings and upkeep are the tree's book-coin figures
(`book_takings`, `book_upkeep`) at the country's cost scale (its civilisation file's `price_index`, `CountryProfile.price_index`) and its
market over long-run prices (`market_factor_at` with `CountryAnswers.price_per_unit`), wages its labour markets' pay
(`pay_per_person_year`). A figure the country keeps no record of (no part of the economy, a trade nobody pays, a concern in a goods
category, whose demand is the home households') makes the reading None and the plant stands idle that year. TEMPORARY HEURISTIC:
no hazard or war factor applies abroad (retire: this complaint). Checks: `sim/tests/test_country_plant_books.py`.

A country's plant takes its crew from that country's labour markets: `CountryWorld.free_fte` is the people its labour markets hold in the
trade (`CountryAnswers.people_of_trade`) less what the other actors of that country employ (`ActorRegistry.staff_fte_in_country`,
`people_left` in `sim/agents/country_state_crew.py`); a country the economy has no part for gives None and the plant finds no crew,
never the founder's pool. The home side counts the same way: the home `free_fte` and `actor_staff_fte` subtract only the home country's
actors' staff (`ActorRegistry.home_staff_fte`, an actor with no country being home), not the foreign actors', whose crew come from their
country's labour. Checks: `sim/tests/test_country_plant_books.py`, `sim/tests/test_home_pool_country_scoped.py`.

A country's plant reads the rest of what running it costs from the same part of the economy (`sim/agents/country_state_site.py`): its site
rent is the hectares the concern occupies at the rent its land market let on the tile (the mean of the land let in the country where none was
let on the tile or the tile is not the country's: `CountryAnswers.land_rent_at`); the manager's hours are paid at the best paid trade of the
crew at the country's pay (`hourly_pay`, used by `firm_entry.management_cost`); the takings of a ramped-up concern (`concern_gross`, which
chooses the entry a state opens) and the yearly costs an entrant weighs (`plant_costs`, behind `business_books.yearly_costs`) are the tree's
book figures at the country's cost scale and prices. A figure the country keeps no record of (no part of the economy, no land let, a trade nobody
pays, a goods category) makes the reading None; the actor does not enter, a state does not open the entry, a plant pays no rent it cannot read,
and a research margin reads as nothing, never the home figure. TEMPORARY HEURISTIC: no hazard or war factor applies abroad (retire: this
complaint). The home world keeps its figures (`hourly_pay` is the home quote, `plant_costs` its upkeep and wage bill). Checks:
`sim/tests/test_country_abroad_readings.py`, `sim/tests/test_country_economy.py`.

**Why it matters.** A country's revenue and war capacity are inputs of the game (481); each of these makes a country's
state read the founder's side of the world or nothing.

**What it would take.** Give each reading a per-country source in the one economy (`economy_port_country.py` answers),
retire the labelled heuristic, then remove the line here. `grep -n "647" sim/agents/country_state.py sim/agents/government.py` lists them.

**Test.** A country's state, given a trade book, a coin stock and its own prices, assesses a customs form and prices the
dole from them; `sim/tests/test_country_state.py` is where the checks go.
