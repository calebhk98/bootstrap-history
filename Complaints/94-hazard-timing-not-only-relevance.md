# Hazard mitigation should show timing, not only relevance

The risk screen was excellent at translating historical danger into actionable categories without exposing the whole tree. However, it only showed which mitigations were relevant, not whether they could be completed in time to matter.

## Why it matters

A mitigation that is known but cannot be completed before the hazard window means the player must already have it operating, or it arrives too late. This timing relationship is crucial for strategic planning but is currently invisible.

## What would resolve it

Improve the risk display with temporal information:

```text
Written corpus helps against knowledge loss.
Earliest possible completion: 1524
Invasion window starts: 1519
-> cannot be ready in time without already-active project

Sanitation reduces plague severity.
Can be completed by: 1510
Plague window starts: 1515
-> sufficient time, currently blocked by: papyrus
```

Show both years until the hazard window and earliest completion time for each known mitigation.

## Where it lives

Likely in `sim/engine/proto/state.py` or a dedicated hazard display module where risk/mitigation information is rendered.

**Confidence:** Design recommendation
