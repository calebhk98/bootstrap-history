# Automation needs a per-turn audit trail

**Status:** partly - `automation [years]` lists each automatic action, and each `step` reply carries the actions of the years it played (`automation` key, one AUTOMATION line on the screen; test `sim/tests/test_ui_step_automation_line.py`); remains (engine, 421): skipped actions with their reason, replace-only versus expand `auto_hire`, the reopening as a policy, tranche payments tied to the mine row

Auto-hire, auto-open, auto-mine, auto-forest and other automation policies can spend money or change staffing. While the policy screen explains the heuristics, the player needs to know what actually happened on this turn and why.

## Why it matters

Without visibility into what automation did, the player cannot diagnose redundant spending (such as commissioning a second mine shaft before the first produced output). The automation systems operate in the background and their decisions are opaque.

## What would resolve it

Show an audit summary for each automation action taken:

```text
AUTO-MINE:
Commissioned 790 t/year coal
Reason: demand 3,100 t/year > active 2,310 t/year
Pending capacity considered: 0 t/year
Cost: 45,000
```

This would make overbuild issues immediately obvious and help the player understand and trust the automation.

## Where it lives

Likely in `sim/engine/core_step_phases.py` where automation runs and decisions are made, and `sim/engine/projects_staffing.py` for staffing automation. Output would go to state or a dedicated automation report.

**Confidence:** Design recommendation

Also reported (Han China 100 AD fog playtest, tester item(s) 77, 84, 85, 171; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): automatic reopening after a staffing closure is unconditional and not a policy (so four concerns reopened "with auto_open off"); `auto_hire` added two ready electricians the year after the player trained two and before they graduated, doubling the trade with no line in the event; `auto_commission` has no receipt of what it bought. The tester wants an annual line listing what each policy hired, reopened, commissioned or skipped, and a replace-only versus expand mode for `auto_hire`. Reproduces: untested live (needs a late game); reopening behaviour confirmed in `projects_staffing.py`.
