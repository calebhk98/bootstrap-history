# Idle directed hours need better late-game handling

**Status:** partly - `idle` shows directed, committed and idle hours, the kind of delay and what could use the hours, and `state` points at it; still open: a sized training and development-program suggestion and a pre-step warning that names the delay kind

In the Rome run, thousands of directed hours per year were often unused while waiting for calendar floors on long projects. A mature optimized civilization can apparently reach vastly larger pools of idle capacity.

The game should make unused organizational capacity impossible to miss and easy to allocate.

## Current state

A one-time tutorial note fires when starting the first multi-year project, explaining that calendar floors are not exclusive research time and spare hours can run other work. The `free_hours_going_unused` field surfaces when all active projects are waiting only on the calendar.

See `sim/tests/test_parallelism_note.py` for the test that verifies this. The field already exists and fires, so this complaint asks for enhancements beyond what is already there.

## What would resolve it

Build on the existing foundation with a more prominent, actionable view:

```text
Directed capacity this year: 11,249 h
Committed to active projects: 4,300 h
Idle: 6,949 h

Potential uses:
- visible zero-cost techniques: 47
- training bottleneck specialists: 320 h
- paid scholarship/work: available
- selected development program: 3,000 h
```

Do not automatically spend the hours. Make it impossible to miss and easy to act on when the player chooses to.

## Why it matters

At large scale, idle capacity represents lost opportunity. The current subtle field is easy to overlook, and the player has no easy path to action.

## Where it lives

Likely in `sim/engine/proto/state.py` where the `free_hours_going_unused` field is already implemented, and `sim/engine/proto/dispatch.py` for actionable suggestions tied to idle capacity.

**Confidence:** Design recommendation

Also reported (Han China 100 AD fog playtest, tester item(s) 218, 223; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): at 400 AD about 11,700 directed founder-hours sat idle each year because every project was calendar- or payment-bound; the tester wanted that capacity pointed at something (more parallel starts, teaching, public services) and deliberately started optional research to use it. Reproduces: untested (late game).

Also reported (final playtests, A and B; `Complaints/reports/final-playtests-triage.md`): both Rome testers had long stretches of unused directed hours while waiting on calendar floors (B: the 24-year power grid), both said the gates themselves are fine and want the wait explained and a way to spend the hours.
