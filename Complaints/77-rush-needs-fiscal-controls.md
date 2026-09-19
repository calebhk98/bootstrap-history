# `rush` needs fiscal controls and strategy modes

`rush limit:10` respected a count limit but nearly emptied the treasury because a "high leverage" item included an ~81k industrial-charcoal project. The command correctly labels itself approximate, but count is not the relevant risk metric.

## WHY IT MATTERS

An automation command that can spend the majority of a player's capital without explicit consent creates both surprise and risk. Players need fiscal guardrails that match their actual constraints.

## WHAT WOULD RESOLVE IT

Add options:

```text
rush limit:10 max_total_cost:20000
rush max_annual_draw:5000
rush reserve_cash:10000
rush mode:cheap
rush mode:food
rush mode:resilience
rush mode:profit
rush mode:institutions
rush mode:broad_unlocks
```

The current downstream-count heuristic is useful but should not be the only definition of leverage.

## WHERE IT LIVES

`sim/engine/proto/dispatch_money.py` or venture command dispatch for `rush` implementation. Likely in `sim/engine/core.py` or projects module for the actual prioritization and cost calculation.

## Confidence

Design recommendation

## Cross-references

Related to UX-005 (batch/multi-select control), UX-006 (development programs), and UX-023 (automation needs audit trail). Together these address automation governance.
