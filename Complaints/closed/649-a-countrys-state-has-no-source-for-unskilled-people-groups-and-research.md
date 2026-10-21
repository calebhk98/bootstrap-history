# A country's state has no per-country source for unskilled people, interest groups, research or a hazard factor

**Status:** closed - every reading of a country's state is its own country's figure or a refusal with a cause; a country's state originating research moved to 676

Follow-up to Complaint 593 (the foreign state is the one `Government`, scoped to its country: `sim/agents/country_state.py`).
A country's `CountryWorld` answers each reading from its profile and its part of the one economy, and refuses (a `NoCountryEconomy`
naming the country, or a refusal `cause`) where it keeps no record; it never answers with the home figure.

**What was left, and what answers it now** (detail in `Complaints/reports/649-history.md`):

- Unskilled people: `national_people` is every working person the country's labour markets hold (`CountryAnswers.working_people`),
  and refuses where they hold nobody; the profile's working age is not read.
- Interest groups: groups form per country from the sectors of its own strata, firms, foundations and servants, read at its own pay
  (`sim/agents/country_groups.py`, `ActorRegistry.consider_groups`); the home state reads only home groups (`ActorRegistry.home_actors`).
- Patronage: the ask is its own clients' (the seats playing in the country that run the funding mechanic) at the country's pay, reach,
  size and real output per head (`sim/agents/patronage.py`, `country_patronage.py`, `agents_port_patronage.py`); a seat of another
  country is paid by that country's state (`Sim.state_funding`).
- Research hands: the people of the family's trades in the country's own labour markets (`CountryCrewView.research_hands`); the start
  gate refuses with the cause `no_country_hands` where the country has no record of them.
- Hazard and war factor: the lowest `output_factor` of the country's own declared hazards running this year
  (`sim/agents/country_hazards.py`), applied to a plant's takings and a concern's gross abroad.
- Trade book: the country's trade is the merchants' carried flows plus what crossed the external edge, kept by country and year
  (`sim/engine/country_trade_years.py`; the counterpart of `foreign_trade_by_year`).
- A firm's income: split among the countries of its operating plants by what each took (`Plant.tile`,
  `sim/agents/taxpayer_income.py`); each state sees the part earned on its tiles.

Tests: `test_country_working_people.py`, `test_country_groups.py`, `test_country_patronage.py`, `test_country_research_hands.py`,
`test_country_output_factor.py`, `test_country_trade_years.py`, `test_firm_income_by_country.py`, and the earlier
`test_country_state.py`, `test_country_economy.py`, `test_country_plant_books.py`, `test_country_abroad_readings.py`.
