# Automation records no skipped actions and auto_hire has no replace-only mode

**Status:** closed - skipped starts, bounties and unordered mines are recorded (`sim/tests/test_automation_skips.py`); `auto_hire` takes a replace-only mode and a mine order id links its audit row, tranche and working (`sim/tests/test_automation_modes.py`)

The UI part of 91 (the audit as a line in each `step` reply) is in `sim/ui`. The rest is engine policy code:

- Done: the project start loop records, through `automation_audit.record_skip`, a candidate costing more than the room left, the active-project cap, and (once a year, for the first one in priority order) a candidate that cannot start; the mine branch records an order of nothing. Rows have action `skipped`.
- Done: `auto_hire` has a replace-only mode (`policy auto_hire replace`). The reopening after a staffing closure stays unconditional; 176 is closed and is not asked again here.
- Done: a mine ordered by auto_mine carries an `order` id from its audit row to its tranche and the working.

Related: 91, 176.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 91 (`closed/91-automation-audit-trail.md`): automation audit trail: what remains is recording skipped actions here.
- 176 (`closed/176-goal-directed-automation.md`): goal-directed automation: `pursue` exists; a policy following stuck's blocker advice, per-goal allocate and auto_hire modes remain.
