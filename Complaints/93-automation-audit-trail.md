# Automation needs a per-turn audit trail

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
