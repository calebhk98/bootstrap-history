# Opening state is informative but overloaded

**Status:** partly - `state` is short by default (situation, what you can do now, goal, risks, then a footer naming the sections), with `state full` and `state <section>` (one section table in `sim/ui/proto/render_screen_state_views.py`); typed `help commands` is a short index of command groups, `help commands <group>` lists one, `help commands all` pages the full listing (`sim/ui/proto/help_commands.py`); unknown commands get fuzzy close matches; test `sim/tests/test_state_help_disclosure.py`; remains: the JSON `{"cmd":"help","topic":"commands"}` still returns the full listing (agents and tests rely on it), and the step reply still renders the full state

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

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 88 (`closed/88-portfolio-bottleneck-centric.md`): portfolio bottleneck view: the remaining piece is one joined dashboard.
