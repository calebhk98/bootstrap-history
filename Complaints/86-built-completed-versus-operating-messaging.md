# "Built/completed" versus "operating" needs stronger transition messaging

`school_founded` completed, but literacy did not begin annual schooling growth until the school was opened/operating. Mechanically this is coherent. The completion wording made it easy to assume the school was already functioning.

## WHY IT MATTERS

Players interpret "built" and "founded" as "ready to use." When an institution requires a separate activation step before effects take hold, the completion message creates a false expectation that leads to missed opportunities or perceived bugs.

## WHAT WOULD RESOLVE IT

Suggested completion message:

```text
School built.
STATUS: CLOSED / NOT TEACHING.
Open it to begin schooling effects and pay upkeep.
```

Do the same for any capability institution whose effects are running-only.

## WHERE IT LIVES

Completion message rendering in `sim/engine/proto/render_screens_big.py` or project-completion handlers. Institution lifecycle and status display logic.

## Confidence

Design recommendation

## Cross-references

Related to UX-016 in the findings. Also relates to UX-008 (boilerplate repetition) - clear one-time messaging about institution lifecycle prevents confusion.
