# Portfolio should become bottleneck-centric at large scale

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
