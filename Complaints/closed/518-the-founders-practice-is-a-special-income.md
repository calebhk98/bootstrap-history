# The founder's practice is a special income instead of a job

**Status:** closed - the founder works a normal job: the hours not spoken for are sold in a held trade at its market wage

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

## Resolution

`practice_income`, `practice_attention`, `practice_note`, the `_your_own_practice` revenue line, the labour screen's
"practice income displaced" and the `work` reply's `it_cost_your_own_practice` / `so_you_are_up` are deleted.

- `sim/labour/labour_job.py`: `hours_for_sale()` is the year's hours less everything spoken for (`director_pool` less
  `director_hours_committed`: teaching, moving, supervising one's businesses, hours sold on request); `standing_job_pay(trade)`
  is those hours at `wage_for_hours`, the market quote `work` already pays. Nothing in it names the founder, so any
  household actor's hours go the same way.
- `held_trade()` (engine) names the trade the founder's held skills give; `founder_wage_income()` hands it to labour. The
  income is one revenue line, `_wages_for_your_own_work`.
- `household.supervision_hours_this_year` is counted in `director_hours_committed`, so supervising hours reduce hours sold
  one for one. Nothing fills it yet: the manager seat of `docs/architecture/FIRMS_OWN_PLANTS_PLAN.md` does.
- `stall_diagnosis` advises wage work only for its gain over the standing job and reads the market wage; the optimizer's
  wage-work fallback compares against the standing job's pay.
- Tests: `sim/tests/test_founder_job.py` (hours times wage, moves with the wage, supervision one for one) and
  `sim/tests/test_founder_job_game.py` (a Rome game, an unhired trade at its quote, revenue follows).
- Measure: `PYTHONPATH=. python3` on a fresh `sim()` Rome game, `revenue_sources()` at turn one and after each
  `step`. Hours your own projects use are still not taken out of the standing job (they ride along, as the practice
  assumed); that is a labelled simplification until project hours are hours of a seat.
- Measured on a fresh Rome opening (`sim()` then `revenue_sources()` and `step` five times; the founder's whole
  income is this one line): turn one 536 before, 326 after; years one to five after the step 519, 477, 419, 397, 434
  before and 315, 289, 254, 241, 263 after. The old line paid the opening schedule's rate with no reputation; the new
  one pays the labour market's quote, which is lower at this opening, and hours spent teaching are now hours not sold.
  The Rome founder's income no longer covers living costs; the opening's wages are the 507 Stage 2 work.
