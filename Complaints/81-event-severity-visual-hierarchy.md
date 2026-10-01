# Event severity needs visual hierarchy

**Status:** partly

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

Also reported (final playtests; `Complaints/reports/final-playtests-triage.md`): three testers ask for the same thing. B: a pinned ALERTS block at the top of every step report for run-ending or costly events (sackings, proscription, eminence or scandal near the line, a concern closing, a project abandoned, a bounty turned into the player's own job); warnings drown in the year report, and output filters in scripts hid the 283 AD sacking until the log was read. A: an optional mode that interrupts time advancement on major historical-risk warnings, a critical business closing, a key employee category gone, a project blocked, a severe failure, a newly unlocked major objective or reaching the goal, returning a structured event. C: a helper script's filtered output nearly hid a sacking in a Rome run. The game already stops `step N` early for some warnings ("stopped after 14 of the 37 years you asked for") but not for these; an ALERTS section at the top of each report, with the stop reasons above, would also serve agents.

**Done:** every step reply carries `alerts` and the step screen prints an ALERTS block first (deaths, goal reached, credit trouble, sackings, losses, closures, abandoned projects, population collapse, early stops), capped and one line each.

**Remains:** the eight-tier severity styling for the event stream itself, and stopping `step N` early for the extra reasons tester A listed (key employee category gone, a project blocked, a severe failure, a newly unlocked objective).
