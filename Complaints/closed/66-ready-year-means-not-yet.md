# A mine's "ready year" reads as this year, and means next year

## What the player saw

A mine was reported as "ready year 1600." At the displayed year-1600 state
it still provided zero capacity; production appeared only after advancing
the year. This contributed to the auto-mine overbuild (`Complaints/65`),
because the wording made the mine appear late when it was not.

## Verified against current code

Confirmed as a real, reproducible turn-order property of the code, matching
the player's own diagnosis that this is a semantics/timing issue rather than
an arithmetic one.

`open_mine()` stamps a tranche's ready year at the moment capital commits
(`sim/engine/economy_mining.py:866`):

    self.household.mine_tranches.append([mat, t_per_yr, self.year + self.MINE_LEAD_YEARS, cost])

`commission_mines()` (`economy_mining.py:870-888+`) activates a tranche once
`self.year >= ready`:

    for tranche in getattr(self.household, "mine_tranches", []):
        mat, amount, ready = tranche[0], tranche[1], tranche[2]
        ...
        if self.year >= ready:
            self.household.mines.append({"material": mat, "capacity": amount, ...})

`commission_mines()` is called from `_step_materials`
(`core_step_phases.py:849`), one of the fourteen `_step_*` phases `step()`
runs in order, and `self.year += 1` is the very last line of `step()`
(`core.py:2187`), after every phase including materials.

That ordering means: the `step()` call that processes what the player is
about to see as "year 1600" runs *while* `self.year` is still 1600 - so a
tranche with `ready == 1600` commissions **during** that same step, and its
new capacity is visible to that step's own material accounting. But the
*next* `state`/`capacity` query the player issues reflects the result of
whichever step already ran; a tranche opened with `ready = 1600` will not
have anything to commission *into* until the step that actually processes
year 1600 runs - which is the step the player triggers by advancing past
whatever year they were looking at when they saw "ready year 1600" in the
first place. In other words, "ready year 1600" is set the moment the
investment is made (at some earlier year), and the capacity becomes visible
only once the *next* turn's step consumes it - exactly the player's
report: querying state at "year 1600" (before that year's own step has run)
shows zero capacity, and it appears once the year is advanced.

Status: **confirmed as the turn-order behaviour the player describes** -
traced through the exact call order (`commission_mines` inside `_step_materials`,
`self.year += 1` at the very end of `step()`), consistent with "ready_year
reads as producing now" being a labelling problem rather than a bug in when
the mine actually commissions.

## Cross-references

Directly related to `Complaints/65` in this batch, as the player's own
document notes - a mine that reads as already active when it is not is one
of the reasons auto-mine's missing `mine_pending` subtraction (`65`) goes
unnoticed by a player trying to reason about why a second shaft was
commissioned. No open complaint in the index names `ready_year` or mine
commission timing specifically; `Complaints/20-training-completion-year.md`
(closed) addressed the identical semantic ambiguity - "ready in YEAR" - for
apprentice training completion, and its resolution is the template this
finding should probably follow, since the two are the same kind of
off-by-one-turn wording problem in two different subsystems.

## What would resolve it

The player's suggested wording fixes are right and cost nothing structurally
- change what the field is called (or add a second one) rather than change
when the mine actually commissions, since the underlying schedule
(`MINE_LEAD_YEARS`, 3.0 years, `economy_mining.py:75-84`) is a real,
intentional modelling choice, not the thing that is wrong:

- Say "commissions during the 1600 turn" rather than "ready year 1600," or
- expose both `ready_year` (when the tranche was scheduled to finish) and a
  clearly-separate `first_full_output_year` (the first year a `state`/
  `capacity` query will actually show its output), or
- follow `Complaints/20`'s resolution pattern directly, since it already
  solved an equivalent problem for training completions in this same
  codebase.

The player's second suggestion - "make automation aware of the same timing
model" - is effectively subsumed by `Complaints/65`'s fix: once auto-mine
correctly subtracts `mine_pending`, it stops needing to reason about
`ready_year`'s wording at all for its own sizing decision, because a
tranche that is pending (regardless of how its ready year is displayed to
the player) already reduces `want` to zero once it covers the shortfall.

## The invariant

Not a bound-style invariant the way most of this batch's findings are; the
closest testable property: a `state`/`capacity` query for year Y, taken
*before* the step that advances past year Y has run, should never claim
capacity that step has not yet added. Concretely: open a mine, advance to
one year short of its `ready_year`, query capacity (assert zero from that
tranche), advance one more year, query again (assert the capacity is now
present) - and assert the field named `ready_year` (or whatever it is
renamed to) is described consistently with which of those two states it
actually promises.
