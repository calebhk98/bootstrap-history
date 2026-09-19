# Project priority should be a first-class editable control

The simulator reports project priorities in the portfolio, but priority management is not prominent enough in the main command discovery flow. Priority matters especially under partial funding when capital is scarce.

## Why it matters

When projects compete for limited resources, priority becomes a first-class strategic lever. Currently it is possible to read and sometimes infer priority, but there is no prominent command to reorder or manage priority bands.

## What would resolve it

Add explicit priority controls such as:

- reorder projects
- priority bands (critical, high, normal, low)
- protect from pause
- mark as background task

Example commands might be:

```text
priority PROJECTID 5
priority all where cost < 1000 set low
protect PROJECTID
```

## Where it lives

Likely in `sim/engine/proto/dispatch.py` and `sim/engine/projects.py` where project state is managed.

**Confidence:** Design recommendation
