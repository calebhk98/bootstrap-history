# Countries other than the home one are static stubs: fixed population, no food, no disease, a one-formula state

**Status:** open - split into 590, 591, 592, 593 (closes when they do)

Only the home country runs the full model. Every other country is a `CountryProfile` read through
`CountryWorld` (`sim/agents/country_view.py`):

- **Population never changes.** `population_total()` returns `self.profile.population`
  (`country_view.py`, `population_total`); nothing assigns it after seeding
  (`grep -rn "profile.population\s*=" sim`). Births, deaths, famine and plague cannot happen abroad.
- **No food or farming.** The farm, granary and nutrition chain (`sim/engine/core.py` around
  `farm_storage.step`, `sim/world/agriculture*.py`) runs for the home country only.
- **No disease.** `sim/engine/disease_port.py` steps one patch: the home nation.
- **Strata are not reconciled to people.** Home strata are held to the population the engine counts
  (`sim/agents/strata_seed.py`, `strata_observed.py`); a foreign country's strata grow by their own rule
  from the seeded figure.
- **The state is one formula.** `ForeignGovernment.revenue` is earners times labourer pay times tax share
  times capacity (`sim/agents/government_foreign.py`). It pays army and officials only: no revenue forms,
  works, navy, dole, reserve policy or borrowing, all of which the home `Government` has
  (`sim/agents/budget.py` `standing_lines`, `sim/agents/revenue.py`).

Why it matters: in a game with several playable countries each one needs the same rules (CLAUDE.md 4.3
and section 2). Today a country's growth, famine, revenue and war capacity are inputs, not outcomes.

What it would take: one `Population`, farm and disease state per country, stepped by the code the home
country uses; retire `ForeignGovernment` in favour of a country-scoped `Government` whose revenue forms
come from that country's civilisation file. Part of 481.

## Split

Children, in order of work:

- 590 (closed): A foreign country's population never changes and its strata grow by their own rule
- 591: A foreign country has no food or farming: the farm, granary and nutrition chain runs for the home country only
- 592: A foreign country has no disease: the disease port steps one patch, the home nation
- 593 (partly done, see 649): ForeignGovernment is one revenue formula: no revenue forms, works, navy, dole, reserve policy or borrowing
