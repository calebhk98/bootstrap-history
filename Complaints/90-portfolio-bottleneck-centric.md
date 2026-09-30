# Portfolio should become bottleneck-centric at large scale

**Status:** open

With 100+ projects active or startable, messages such as "priority #129 of 181" cease to be useful for decision making. The valuable information becomes aggregate trade pressure and resource consumption: for example, "Scribes: 9,034 h demand / 8,939 h supply, affecting 18 projects."

## Why it matters

At large scale, individual project prioritization is less important than understanding which resources are constraining multiple projects at once. The current per-project view becomes verbose noise when what the player needs is visibility into which bottleneck has the highest leverage.

## What would resolve it

Show resource pools and constraints first in portfolio view:

- director hours
- scholars
- scribes
- craftsmen
- chemists
- machinists
- capital draw
- key materials (coal, iron, copper)
- power

Let the player drill into the projects consuming each bottleneck to pause, reprioritize, or retrain as needed.

## Where it lives

Likely in `sim/engine/proto/dispatch.py` and `sim/engine/proto/render_screens_economy.py` where the portfolio command is rendered.

**Confidence:** Design recommendation

Also reported (Han China 100 AD fog playtest, tester item(s) 57, 80, 191; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): `portfolio` showed `calculus 800 hours total to go` at 60 percent complete, annual demand 37,035 against requests of 10,000, priorities "2 of 3" and "3 of 3" with two projects active, a 1,100-hour budget from the previous resolution, and grid 900 hours to go while `state` said all hours spent; the tester could not tell last year's allocation from this year's forecast. Related 206. Reproduces: untested (needs several concurrent late projects).
