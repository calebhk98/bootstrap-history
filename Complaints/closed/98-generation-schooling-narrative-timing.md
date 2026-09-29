# "A generation of schooling..." can be narratively wrong immediately after schools open

When a school is first opened, the first logged schooling change can occur shortly after, but the log message says:

> "a generation of schooling shows in the census"

This wording implies decades of operation that did not happen, and is narratively inaccurate if the school was just opened this year.

## Why it matters

Narrative accuracy matters for player understanding. A message that claims a generation has passed when only a year has is misleading about how education actually accumulates over time.

## What would resolve it

Base the wording on institution age rather than using a generic phrase:

- **Early (year 0-5):** "schooling is beginning to show in the census"
- **Later (year 5+):** "a generation of schooling shows in the census"

Or use more precise language:

- "schooling effects emerging" vs. "full generational effect"

## Where it lives

Likely in `sim/engine/society.py` in the `_advance_literacy()` method where the 25-year log throttle message is generated.

**Confidence:** Design recommendation

**My note:** This is a low-impact realism issue with UX flavor. Easy to address once literacy logging is touched for other reasons.
