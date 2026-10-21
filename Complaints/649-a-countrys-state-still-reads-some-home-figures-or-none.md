# A country's state still reads some home figures, or none: no trade book, coin stock, prices, equipment, trade counts or research hands of its own

**Status:** open (partly done: prices and coin read the country's own part of the economy; the rest below remains)

Follow-up to Complaint 593 (the foreign state is now the one `Government`, scoped to its country; `sim/agents/country_state.py`).

**What is wrong.** The home `Government` reads the home-only engine; a country's `CountryWorld` now answers most of those
readings from its profile and its part of the one economy, but these have no per-country source yet:

- Trade book: `trade_value` is zero abroad, so a declared `imports_value` or `exports_value` form yields nothing.
- Equipment: `equipment_kg_per_soldier` is the home diffusion of the founder's military work.
- People by trade: `national_people` is the working age for every trade (labelled heuristic in `country_state.py`).
- Rent owners: `land_rent_owners` names nobody, so a land-rent form is drawn from the edge.
- Interest groups and patronage: `group_claims` is empty and `patron_ask` is zero abroad.
- Research: a country's state copies but does not originate research (`Government.researches`), as research hands are the founder's.
- State enterprises and monopolies declared in a country's file run against the founder's concerns.
- Taxpayers: a country's visible taxpayers are its firms only; seats of that country are not listed.

**Done.** A country's `material_cost` and `material_price` are its own market areas' quote (`CountryAnswers.price_per_tonne`,
nothing where they quote none); its `coin_regime` is the one economy's money standard and its `coin_stock_value` is the
backing metal in the money held on its tiles at its own price of that metal (`country_figures.money_held`). Checks:
`sim/tests/test_country_state.py`, `sim/tests/test_country_economy.py`.

**Why it matters.** A country's revenue and war capacity are inputs of the game (481); each of these makes a country's
state read the founder's side of the world or nothing.

**What it would take.** Give each reading a per-country source in the one economy (`economy_port_country.py` answers),
retire the labelled heuristic, then remove the line here. `grep -n "647" sim/agents/country_state.py sim/agents/government.py` lists them. The trade book needs
the merchants' carried flows kept by good (`record.carried` is tonnes by tile pair only) so they can be valued at each side's price.

**Test.** A country's state, given a trade book, a coin stock and its own prices, assesses a customs form and prices the
dole from them; `sim/tests/test_country_state.py` is where the checks go.
