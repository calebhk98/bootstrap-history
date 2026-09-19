# Mature play needs a "development program" abstraction, not hundreds of individual clicks

Once the economy and institutions were mature, the meaningful decision became "Commit up to 200k capital and ~15k directed hours to broad visible development over the next several years." The UI still operates primarily at individual-project granularity.

## WHY IT MATTERS

Late-game strategy is fundamentally different from early-game. Early players build individual concerns. Late players set portfolio policies. The UI does not adapt, forcing manual micromanagement of hundreds of items to express a single high-level decision.

## WHAT WOULD RESOLVE IT

Allow a development program with:
- category priorities
- maximum total capital commitment
- maximum annual cash draw
- maximum director-hour commitment
- reserve cash floor
- excluded categories/projects
- pause conditions if debt, war risk, or resource shortages exceed thresholds

The player remains the strategist; the program handles clerical scheduling.

## WHERE IT LIVES

`sim/engine/proto/dispatch.py` for command parsing and program definition, `sim/engine/core.py` or project management systems for program execution and scheduling logic.

## Confidence

Design recommendation

## Cross-references

Related to UX-005 (batch start), UX-031 (idle directed hours), and UX-020 (portfolio bottleneck-centric view). Together these address the shift needed for mature-play UX.
