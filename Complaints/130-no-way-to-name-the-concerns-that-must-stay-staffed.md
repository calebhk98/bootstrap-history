# No way to name the concerns that must stay staffed through attrition

**Status:** open

**Source:** `reports/TOP_PROBLEMS.md` item 9 and `reports/PLAYTEST_LOG_ROME_100_BLIND.md` observations 201 and 244.

## What is wrong

Normal attrition repeatedly closed critical concerns (power grid, lead chamber,
zinc, interchangeable manufacture) because nobody was left to supervise them.
`auto_hire` is deliberately simple and has no notion of which concerns matter,
so the player rehires by hand every time. The report asks for a small priority
list ("keep these N concerns open"), not more automation.

## Evidence

- `sim/engine/core.py` policy defaults (`auto_hire`, `auto_open`,
  `auto_mothball`): whole-portfolio switches, no per-concern choice.
- `Complaints/89` asks the state screen to call out specialist-caused closures;
  this issue is the control that would prevent them.

## Why it matters

Whack-a-mole maintenance is UI cost, not strategy, and a silent closure of a
supply concern cascades into downstream projects.

## What it would take

A per-concern `keep_staffed` flag (settable through `policy` or `mothball`
style command) that `auto_hire` and the attrition step honour first: hire or
hold the supervisors for flagged concerns before any others, and refuse to
`auto_mothball` them. It is actor-general, so it belongs on the household actor
rather than on the founder. Regression test: attrition removes a supervisor,
flagged concern stays open, unflagged one closes.
