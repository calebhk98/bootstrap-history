# A payroll the household can only partly pay is kept whole

**Status:** closed - the check's setup was wrong, not the staff step; `round2_policy_hazards_options` "an unaffordable payroll is trimmed to what you can pay, not emptied" now sets the means the way the step measures them

`round2_policy_hazards_options` check "an unaffordable payroll is trimmed to what you can pay, not
emptied" fails. A household with auto-hire off holds five smiths and means for living costs plus a bit
over half the payroll. After one step it still holds all five (5.00 -> 5.00), where the check expects
some to be let go.

This predates the labour-market work: the same scratch reproduction gives 5.00 -> 5.00 at `d9e3295`.
The reproduction is the check's own setup, at `sim/tests/test_round2_policy_hazards_options.py`
around line 1029, run alone.

Either the trimming rule no longer fires, for example because wages or credit now leave enough room on
paper, or the check's arithmetic for "half the payroll" no longer matches what the step charges.

What it would take: print the room the staff step computes against the payroll in that case. That is in
`sim/engine/step_phase_staff.py` and `labour.wage_bill`. Then decide which of the two is wrong.

Resolution: the staff step measures what can be paid as revenue less upkeep, mining and non-wage living
costs, plus the credit left. The check set capital as living costs plus part of the payroll, ignoring revenue
and upkeep, so the step rightly found the whole payroll affordable (the printed room, compared with the
payroll, shows it). The check now settles capital until the step's own measure of the means is a bit over
half the payroll, and the trimming rule fires as designed.
