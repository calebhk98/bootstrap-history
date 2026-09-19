# "School" is overloaded for two different mechanics

"Buy school smith 2" refers to trade-training capacity (apprenticeship seats), while "school_founded" is a general-literacy institution that teaches the population as a whole.

For a literacy-focused run this creates confusion because the same word means completely different things in these two contexts.

## Why it matters

A player focused on reaching a literacy goal sees "school" in multiple places and cannot easily distinguish whether they are managing trade-training capacity or population education. The naming inconsistency makes it harder to understand which system affects the goal metric.

## What would resolve it

Rename trade-specific training capacity in high-level UI to one of:

- apprenticeship school
- trade school
- training capacity
- guild training seats

Reserve "school" in high-level UI and goal contexts for population education institutions that drive general literacy.

## Where it lives

Likely in `sim/engine/proto/dispatch.py` and `sim/engine/projects.py` where "school" purchase commands are defined, and in `sim/engine/core.py` where schooling effects compute.

**Confidence:** Design recommendation
