# Opening state is informative but overloaded

**Status:** partly - `help commands` opens with a short beginner index and the welcome screen points at it and at `help sittings`; the `state` screen now reads money and hours, shortages, goal, looming risks, then running work, staff and standing (test `sim/tests/test_small_screen_items.py`). Remains: no progressive disclosure (the full detail still prints in one screen, no collapsed advanced section) and `help commands` is still the full listing without pagination

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

Likely in `sim/ui/proto/state.py` where the opening state is rendered, with structure decisions in `sim/ui/proto/dispatch.py`.

**Confidence:** Design recommendation

Also reported (Han China 100 AD fog playtest, tester item(s) 8, 12, 64; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the first screen and `help commands` print a couple of hundred lines of reference (every alias, every usage) and the five-command introduction does not say `help commands` has a beginner index; the tester wanted a short index, pagination and aliases on request. Reproduces: yes (`help commands` at the first prompt).

Also reported (final playtests, B; `Complaints/reports/final-playtests-triage.md`): in-game `help sittings` explains one-command-per-process play (the README's Saving section shows it) and the game itself notes that most agents miss it; B asks for a pointer to it from `help` or the first screen. Reproduces: yes (the start screen lists `help` topics in a paragraph; `sittings` is one of thirteen).
