# A payroll the household can only partly pay is kept whole

**Status:** open

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
