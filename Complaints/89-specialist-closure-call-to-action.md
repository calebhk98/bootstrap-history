# Specialist-caused venture closures need a direct call to action in state

Auto-hire could replace general labor after attrition while a profitable concern stayed shut because it specifically needed a carpenter or foreman FTE. The detailed venture screen explains this specialist requirement, but the high-level state output did not make the specialist cause prominent enough to prompt action.

## Why it matters

A player seeing a closed profitable concern in state has to navigate to the venture screen to discover why it is closed. If the closure is due to a specific specialist shortage, this should be visible immediately so the player can decide whether to hire, train, or reprioritize.

## What would resolve it

Add a direct call-to-action line to state output:

```text
1 profitable concern shut:
- Toy workshop: missing 0.25 carpenter FTE
```

This is much more actionable than a generic "you know how to run 6 more concerns" message.

## Where it lives

Likely in `sim/engine/proto/state.py` where the main state summary is built, and `sim/engine/projects_staffing.py` where specialist requirements are tracked.

**Confidence:** Design recommendation
