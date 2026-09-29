# Starting a project does not warn that its finished concern could not be opened

**Status:** open

**Source:** `reports/TOP_PROBLEMS.md` item 10 (build staffing versus operating staffing).

## What is wrong

A concern's build crew and its operating supervision are different numbers
(`venture_hands` charges a fraction of the build crew as supervision). A
player can afford and complete a project, then find that today's free staff
could not open it. `why` shows both numbers, but inside a very long page.

## Evidence

- `sim/engine/projects_ventures.py:91` (`venture_hands`) computes the operating
  supervision; `sim/engine/projects_starting.py:858` (`start_project`) does not
  compare it with free staff at start time.
- `python3 sim/simulator.py why <big concern>`: build staff and operating
  staff appear as two separate lines.

## Why it matters

The surprise arrives years after the decision, when the cost is already sunk.

## What it would take

At `start`, compare the concern's operating supervision with the free staff
that would exist at completion and, when short, say so in the start message
("you can build this now, but with today's staffing you could not open it").
Advisory only, never a refusal. Regression test: a start with insufficient
free supervision carries the warning; one with enough does not.
