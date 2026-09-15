# Expected calendar time can be less than the hard calendar floor

**Type:** Displayed-math bug  
**Priority:** High

## Player evidence

Observed examples: `corpus_written` 10y floor / 6.75y expected; blast furnace 5y / 3.89y; kinetic theory 6y / 3.56y; interchangeable parts 8y / 5.17y; industrial zinc 12y / 7.77y.

## Expected behavior

Expected completion time for an unstarted project cannot be shorter than its irreducible floor.

## Suggested check

Correct the retry expectation formula or label the displayed field as something other than total calendar completion time.
