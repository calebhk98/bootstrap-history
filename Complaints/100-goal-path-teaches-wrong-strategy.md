# Goal/path UI can accidentally teach the wrong strategy

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

Likely in `sim/engine/proto/techtree.py` and `sim/engine/proto/dispatch.py` where goal/path information is rendered.

**Confidence:** Design recommendation
