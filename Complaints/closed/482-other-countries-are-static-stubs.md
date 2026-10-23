# Countries other than the home one are static stubs: fixed population, no food, no disease, a one-formula state

**Status:** closed - umbrella; every child is done or moved: remaining work lives in 649

Only the home country used to run the full model; other countries were a `CountryProfile` read through `CountryWorld`
(`sim/agents/country_view.py`). Children:

- 590 (closed): a foreign country's population never changes and its strata grow by their own rule
- 591 (closed): a foreign country has no food or farming
- 592 (closed): a foreign country has no disease
- 593: ForeignGovernment is one revenue formula; the class is gone (`grep -rn ForeignGovernment sim` is empty) and a
  country is a scoped `Government` (`sim/agents/country_state.py`). The readings that still use home figures are 649.
- 594, 595 (closed): a country seat and orders from it

Why it mattered: in a game with several playable countries each one needs the same rules (CLAUDE.md 4.3 and
section 2). Part of 481.
