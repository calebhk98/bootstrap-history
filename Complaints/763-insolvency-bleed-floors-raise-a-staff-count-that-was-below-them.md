# Insolvency's bleed floors raise a staff count that was below them

**Status:** open

When a household has been insolvent long enough and sits deeper in arrears than its floor, the money phase thins its staff:
`artisans = max(INSOLVENCY_ARTISAN_FLOOR, artisans * (1 - bleed))` and
`scholars = max(INSOLVENCY_SCHOLAR_FLOOR, scholars * (1 - bleed * INSOLVENCY_SCHOLAR_BLEED_DISCOUNT))`
(`sim/finance/insolvency.py`, `Insolvency.judge_insolvency`; it was in `sim/engine/step_phase_money.py` before the finance
module). The floor is meant to stop the bleed ("a household that has shed everything else can still climb back"), but `max`
also lifts a count that was already below it: a household with no artisans and no scholars that is insolvent for the
third year ends the year with three artisans and one scholar, people the household never hired and does not pay for.

Evidence: with `FinanceSeat(insolvent_years=3)`, `acting_balance=-1e12`, `artisans=0.0`, `scholars=0.0` and no revenue,
`finance_host.build(...).judge_insolvency()` leaves `artisans == 3.0` and `scholars == 1.0`
(`sim/tests/finance_host.py`; the case is not in `sim/tests/test_finance_module.py` because the move keeps the behaviour).

Why it matters: staff appear from nothing in the year a household is worst off, which both flatters an insolvent run
(the new hands work and are paid for from its revenue) and breaks the rule that a headcount comes from hiring, training or
birth. It would also hide a real loss of the last staff.

What it would take: `min(count, max(floor, count * (1 - bleed)))`, so the bleed never raises a count, with a regression test
on a household below the floor; then re-record the micro equivalence baseline, since a run that hits it changes.
