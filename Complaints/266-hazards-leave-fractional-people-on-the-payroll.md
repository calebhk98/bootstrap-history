# Sacks and epidemics leave "0.55 carpenters" and "0.4 scribes" on staff

**Status:** open

C: fractional headcounts after sacks and plagues in all three runs.

Cause: attrition rolls every person separately ("PEOPLE ARE WHOLE", `sim/engine/core_step_phases.py`), but the hazard code scales every headcount by a fraction: `_shock_staff_loss` does `household.employees[trade] *= (1 - loss)`, scholars, artisans and `directors_extra` likewise, and the sack does the same with `SACK_STAFF_RETENTION` (`sim/engine/society_hazards.py`). Nothing rounds back to people afterwards, so a foreman test ("needs 0.25 carpenter FTE") and a closure rule see 0.55 of a person. Code reading; the harness confirms the multiplication on any integer staff.

What it would take: round each trade's loss with the same per-person rolls the attrition uses, so staff stays whole, or document the fraction as a part-time share. Related: 235, 70 closed, 168 closed.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bug 9). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
