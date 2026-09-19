# Opening state is informative but overloaded

Before the player makes their first decision, the initial state output can expose them to:

- saves/sessions
- logs
- policy/automation settings
- fog status
- eminence
- risk
- staffing/training
- unused hours
- goal progress
- large available-tech counts

Each piece is individually useful, but the hierarchy is weak. A new player sees no clear priority signal for what to read first or what to decide first.

## Why it matters

Cognitive load at game start is high. Without clear hierarchy, the player cannot easily understand what requires immediate attention versus what can be explored later. This contributes to confusion about what the first action should be.

## What would resolve it

Use progressive disclosure with a clear hierarchy:

1. **Situation and immediate constraints** - what is different today, what is the critical bottleneck
2. **Current decision resources** - capital, hours, labor available right now
3. **Goal** - what you are trying to achieve
4. **Looming risks** - what could go wrong soon
5. **Advanced systems** - detailed breakdowns, help, policy settings (on demand)

Example structure:

```text
YEAR 1 AD — Rome

IMMEDIATE SITUATION
Population: 2.1M
Capital: 50,000
Directed hours available: 200/year
Critical bottleneck: none yet

WHAT YOU CAN DO NOW
Start techniques, open projects, adjust policy...

YOUR GOAL
Junction transistor (15 prereqs discovered)

LOOMING RISKS
None in next 10 years

[policy] [risk] [details]
```

## Where it lives

Likely in `sim/engine/proto/state.py` where the opening state is rendered, with structure decisions in `sim/engine/proto/dispatch.py`.

**Confidence:** Design recommendation
