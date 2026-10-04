# Goal/path UI can accidentally teach the wrong strategy

**Status:** partly - `leverage` and `path` show the system levers; `stuck` adds a lever line, says when every goal-route project is waiting on the calendar and suggests side work, and marks the cheapest-startable suggestion as filler (`sim/ui/proto/stuck_advice.py`, test `sim/tests/test_portfolio_scale_stuck_advice.py`); remains: an optional warning before a multi-year step with many unused hours and startable projects, beyond the existing `multi_year_hours_warning` case

The Rome transistor run became extremely inefficient because the visible goal/path information encouraged a direct prerequisite-chain mindset. The player focused on completing prerequisites in order rather than building a strong civilization first.

The game's actual optimal strategy is often:

> improve the civilization broadly so the goal becomes cheap, fast, and robust.

This is a good emergent property, but the UI should help players realize it rather than encouraging the opposite approach.

## Why it matters

A player who understands system leverage (literacy, labor, finance, health, institutions) can reach any goal much faster than one following the direct prerequisite chain. Currently the UI can mislead new players into the inefficient approach.

## What would resolve it

For a hard goal, show system-level leverage rather than just the prerequisite chain:

```text
GOAL: Junction transistor

Direct prerequisites: 15 known
Estimated completion following chain: 320 years

KEY LEVERAGE POINTS
- Literacy: unlock faster research
- Labor: enable parallel projects
- Finance: remove cost bottleneck
- Institutions: increase specialization
- Knowledge preservation: protect against loss
- Material capacity: ensure supply chains
```

Suggest that a broad approach can make the goal cheaper and faster, without prescribing a specific tech route.

## Where it lives

Likely in `sim/ui/proto/techtree.py` and `sim/ui/proto/dispatch.py` where goal/path information is rendered.

**Confidence:** Design recommendation

Also reported (Han China 100 AD fog playtest, tester item(s) 29; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): during deliberate saving years `stuck` answered "'start civ_glass_windows' would begin the cheapest thing you can pay for today" (replayed: yes, at the very start), which nudges a player toward collecting free filler; the tester asks to mark a planned project and savings target so the adviser respects it and shows the year it becomes affordable under current income. Reproduces: yes for the advice.

Also reported (final playtests, A and B; `Complaints/reports/final-playtests-triage.md`): B ('idle waiting'): several stretches (the 24-year power grid, an 11.8-year floor) had nothing forced to do, and nothing nudges the player toward side goals or coverage work; asks that when every goal-path project is calendar-bound the game says so and suggests them. A made the same point from the other side: advancing the calendar while waiting was their mistake and the time gates should not be removed, but the interface should distinguish kinds of delay and warn, optionally, before advancing several years with many unused hours and startable projects (`step N` already warns in one case, see `sim/ui/proto/dispatch.py`, `multi_year_hours_warning`).
