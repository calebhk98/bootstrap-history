# Workshop forecast contradicts realized revenue

**Status:** closed - pinned by sim/tests/test_round2_policy_hazards_options.py

**Type:** Financial forecast/UI defect  
**Priority:** High

## Player evidence

`why workshop_first` and `open` both said the workshop earned 0/year and cost 900/year. Immediately after opening, `money` added 1,783/year workshop revenue and recurring net rose sharply.

## Why it matters

The player delayed activation based on the displayed financial consequence of a major institution.

## Suggested check

Expose expected indirect/output revenue before opening, or clearly label it as an undisclosed/variable effect.
