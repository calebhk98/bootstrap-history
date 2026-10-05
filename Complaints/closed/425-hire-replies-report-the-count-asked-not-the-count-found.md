# Hire replies and the staff audit report the count asked for, not the count found

**Status:** closed - `hire_reports_count_found` (the hire reply and the staff audit row name the people the staff gained; the reply also carries `asked`).

A hire now takes only the people the local market can supply this year (Complaint 271). The rule is
`LabourMarket.whole_recruits`. `hire_check` returns the count found, and the `hire` reply says "Found N
of the M asked for". Two callers outside `sim/labour/` still report the number asked for:

- `sim/ui/proto/dispatch_labour.py`: the hire reply echoes `n`, so a partial fill reads as a full one. It
  should report the count from `hire_check`, which `quote_spending.py` already shows as `people`. The
  quote screen (`_quote_hire`) could also say how many must be sought next year.
- `sim/engine/step_phase_staff.py` `_grow_to`: the audit record says `int(delta)` hired. It should use the
  change in the employer's headcount.

What it would take: read the found count in both places. No change in `sim/labour/` is needed.
