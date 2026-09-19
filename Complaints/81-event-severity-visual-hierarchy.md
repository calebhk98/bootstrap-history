# Event severity needs visual hierarchy

A tiny failed technique and a civilization-scale population collapse could appear at similar prominence.

## WHY IT MATTERS

Without visual distinction by severity, players cannot quickly identify what actually matters. A log where all events have equal weight fails to direct attention and fails to communicate the scale of consequences.

## WHAT WOULD RESOLVE IT

Suggested tiers:
- informational
- project completion
- minor setback
- major project failure
- economic crisis
- demographic catastrophe
- regime/war/sack catastrophe
- run-ending event

The event stream should optimize attention, not chronological equality.

## WHERE IT LIVES

Event rendering and styling in `sim/engine/proto/render_screens_big.py` or event-display modules. Event classification logic in core engine or event-generation systems.

## Confidence

Design recommendation

## Cross-references

Related to UX-010 (one event per disaster - grouping), UX-012 (large completion waves summary-first), and UX-013 (tiny failures should not get major weight). These three together address event presentation hierarchy.
