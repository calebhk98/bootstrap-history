# The founder's practice is a special income instead of a job

**Status:** open - owner decision (2026-10-14): the founder works a normal job

The founder earns `practice_income` from skills the society holds (`granted`), shown as the `_your_own_practice`
revenue line, and the labour screen nets wage work against "practice income displaced"
(`sim/labour/labour_wage_ledger.py`). No other actor has a practice; it is a founder-only income with its own
formula. Measure its readers: `grep -rn "practice_income\|_your_own_practice" sim --include=*.py`.

Owner decision: the practice is the founder working a normal job. The founder offers hours in the labour market in a
trade they hold (their skills may give them a trade others lack, at that trade's wage) and is paid like any worker;
hours spent supervising their own businesses (the manager seat in `docs/architecture/FIRMS_OWN_PLANTS_PLAN.md`) are
hours not sold. What it would take: route the founder's hours through the labour market as a household's, delete
`practice_income` and its screens' special lines, and keep the `stuck` and wage-work advice reading the market wage.
Tests: a founder's earned income equals hours sold times the wage of the trade, and changes with that wage.
