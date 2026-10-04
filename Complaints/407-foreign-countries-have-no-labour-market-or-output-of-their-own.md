# Foreign countries have no labour market or output of their own: their wages and output are the home ones rescaled

**Status:** open

An actor of a foreign country sees `CountryWorld` (`sim/agents/country_view.py`). It answers several
questions by scaling the home answer with the country's profile:

- **Pay** is the home labour market's quote times the country's `wage_index` over the home one.
- **Output** is home output per head times the country's population and relative wage level.
- **Food** is scaled by relative `price_index`, and **housing** by relative wage level.

`sim/tests/test_one_labour_market.py` holds the rule that no module outside the labour market computes
a wage. The pay above breaks that rule in spirit, and is labelled as a temporary heuristic where it
stands. The AST check in that test looks for a direct `.wage_index` product, so it does not catch the
helper used here.

This matters because foreign governments' revenue, foreign strata incomes and a foreign firm's wage
bill all rest on these figures.

What it would take: each country's own labour market (a `sim/labour/` market per country, or one
market that quotes per country), and its own output measure. The partner economies of Complaint 382
step 4 would supply both. `CountryWorld` would then forward these questions to the country's own
market, not rescale the home one.
