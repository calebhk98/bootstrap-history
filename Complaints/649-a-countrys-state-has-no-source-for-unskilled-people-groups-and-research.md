# A country's state has no per-country source for unskilled people, interest groups, research or a hazard factor

**Status:** partly - prices, coin, trade book, people by trade, equipment, rent owners, taxpayers, plant books, crew, site rent, manager pay and entry costs read the country's own part of the economy; the items below remain

Follow-up to Complaint 593 (the foreign state is the one `Government`, scoped to its country: `sim/agents/country_state.py`).
Code that waits on this complaint carries `retire: Complaint 649`: find it with `grep -rn "Complaint 649" sim`.

**What is wrong now.** A country's `CountryWorld` answers most readings from its profile and its part of the one economy
and answers None, never the home figure, where it keeps no record. These have no per-country source yet:

- Unskilled people: `national_people("labourer")` is the working age, as at home (a labelled heuristic in `country_state.py`,
  also used for a country the economy has no part for).
- Interest groups and patronage: `group_claims` is empty and `patron_ask` is zero abroad (`country_state.py`).
- Research: a country's state copies research but does not originate it (`Government.researches`, `sim/agents/government.py`;
  research hands are the founder's).
- No hazard or war factor applies to a plant abroad (a temporary heuristic in `business_plant_books.py` and
  `country_state_site.py`, retire here).
- A firm has one country (`ActorRecord.country`), so its taxable income is not split by where its plants earn; splitting it
  needs a tile on each plant and the country of that tile (`setup.country_of`).
- The country's trade book counts the merchants' carried goods only; the home state's `foreign_trade_by_year` (trade with
  off-map partners) has no country counterpart.

**Why it matters.** A country's revenue and war capacity are inputs of the game (481); each of these makes a country's state
read the founder's side of the world or nothing.

**What it would take.** Give each reading a per-country source in the one economy (`economy_port_country.py` answers),
retire the labelled heuristics, then remove the line here. Test: a country's state, given its own figures, assesses a
customs form and prices the dole from them (`sim/tests/test_country_state.py`).

**Built (one line each; detail in `Complaints/reports/649-history.md`).** Prices and coin stock (`country_figures.money_held`);
the trade book from `record.carried_goods` (`sim/economy/carried_book.py`, `country_figures.trade_book`); people by trade
(`CountryAnswers.people_of_trade`); equipment burden by the country's own knowledge; rent owners along the country's own
rent curve; seat and firm taxpayers by country; plant books at the country's cost scale (`world.plant_books`); crew from the
country's labour markets (`CountryWorld.free_fte`); site rent, manager pay and entry costs from its own market
(`sim/agents/country_state_site.py`). Tests: `test_country_state.py`, `test_country_economy.py`, `test_carried_book.py`,
`test_country_plant_books.py`, `test_country_abroad_readings.py`, `test_home_pool_country_scoped.py`,
`test_home_state_taxpayers.py`.
