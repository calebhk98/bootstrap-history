# ForeignGovernment is one revenue formula: no revenue forms, works, navy, dole, reserve policy or borrowing

**Status:** closed - the class is gone and a country is a scoped `Government`; what a country's state still reads as a home figure or as nothing is tracked in 649

Part of Complaint 482 (Countries other than the home one are static stubs).

Depends on 590 (earners counted). Blocks 594 and 595.

**What is wrong.** `ForeignGovernment.revenue` is earners times labourer pay times tax share times capacity, and the state pays army and officials only.

**Evidence.** `sim/agents/government_foreign.py`; the home `Government` has revenue forms, works, navy, dole, reserve policy and borrowing (`sim/agents/budget.py` `standing_lines`, `sim/agents/revenue.py`).

**Why it matters.** A country's revenue and war capacity are inputs, not outcomes, and a player cannot hold a country whose state is one formula (481).

**What it would take.** Retire `ForeignGovernment` in favour of a country-scoped `Government` whose revenue forms come from that country's civilisation file. Delete the class, do not wrap it.

**Test.** `grep -rn ForeignGovernment sim` is empty; a foreign country's revenue is assessed from its declared forms in `data/civilizations/`; the home `Government` topics pass unchanged for a non-home country.

## What was done

- `ForeignGovernment` and `government_foreign.py` are deleted; `grep -rn ForeignGovernment sim` is empty. The cast seeds every
  country's state as a `Government` with the country set (`sim/agents/cast.py`). The export-policy and market-closing
  methods moved to `sim/agents/government_markets.py`.
- A civilisation's `state_revenue` (and `hazards`) is carried into the country's profile; `CountryWorld` answers the readings the
  home Government takes from the home engine through `sim/agents/country_state.py`: revenue forms and their bases
  (harvest from the country's farm, people from its cohorts, tiles, territory), the army wanted and under arms, its levy
  (its own capacity, tax share and shortfall rates), payroll to its own strata, purchases paid at once, no founder labour pool.
- The engine's `notice_over`, `levy_shares`, `fleet_goods` and `state_may_borrow` take the country's figures
  (`sim/engine/agents_port*.py`, `society_state_pressure.py`).
- Effect on the game: a foreign state now has the home state's budget lines (collectors, public buildings, court, dole, navy,
  works), so it can be short of money where the one formula was not; its revenue is its declared forms, not earners times pay.
- Still open: `649` lists what a country's state reads as nothing or as a home figure.

**Tests:** `sim/tests/test_country_state.py` (revenue assessed from declared forms; the same budget lines as the home state for the same inputs;
a year of the state), `sim/tests/test_agents_countries.py`, `sim/tests/test_state_headcount.py`.
