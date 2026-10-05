# Automation records no skipped actions and auto_hire has no replace-only mode

**Status:** partly - skipped starts, bounties and unordered mines are recorded (`sim/tests/test_automation_skips.py`); `auto_hire` modes and tranche linkage remain

The UI part of 91 (the audit as a line in each `step` reply) is in `sim/ui`. The rest is engine policy code:

- Done: the project start loop records, through `automation_audit.record_skip`, a candidate costing more than the room left, the active-project cap, and (once a year, for the first one in priority order) a candidate that cannot start; the mine branch records an order of nothing. Rows have action `skipped`.
- `auto_hire` has no replace-only versus expand mode, and the reopening after a staffing closure is unconditional rather than a policy (176 asks for both).
- A mine's later tranche payments are not tied back to the row that ordered it.

Related: 91, 176.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 91 (`closed/91-automation-audit-trail.md`): automation audit trail: what remains is recording skipped actions here.
- 176 (`closed/176-goal-directed-automation.md`): goal-directed automation: `pursue` exists; a policy following stuck's blocker advice, per-goal allocate and auto_hire modes remain.
