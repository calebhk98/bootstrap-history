# `path` prints one lifetime budget and judges against a different one

**Type:** Bug, player-facing
**Priority:** Medium. It is two lines apart and it tells the player the opposite of what it just told them.

Found by the agent migrating `sim/engine/cli.py`'s constants, which is the
point of that exercise: a literal nobody had to name is a literal nobody had
to reconcile.

## 1. 60,000 against 72,000

`cmd_path`, consecutive statements:

```python
print("\nFounder-hours available in one lifetime at 2000/yr for 30 yrs: 60,000")
print("Founder-hours demanded by this path : %s" % f"{cum_ph:,.0f}")
print("=> %s" % ("feasible alone in principle, but not with the calendar floors"
                 if cum_ph < FOUNDER_LIFETIME_HOURS else
                 "IMPOSSIBLE for one person..."))
```

`FOUNDER_LIFETIME_HOURS` is 72,000. The sentence above it says 60,000, and
shows its working: 2,000 hours a year for 30 years. That arithmetic is
right. The threshold is not.

So a path demanding 65,000 founder-hours is told, in order, that it has
60,000 available, that it needs 65,000, and that this is **feasible alone**.

The same 72,000 appears again in `cmd_why`'s "% of a 72,000-hour life".

## Where 72,000 came from

2,400 x 30 = 72,000 exactly, and `sim/engine/data.py`'s own comment on
`founder_hours_per_year` records that the founder used to be modelled at
2,400 hours a year and was deliberately moved to 2,000: *"2,000, NOT 2,400
... twenty per cent more than a hired man"*. The prose was updated to match
the new figure. The threshold was not. It is a relic with a 20% error in the
direction that flatters the player.

## 2. The mortality sweep runs at half the real variance

`cmd_sweep`'s mortality axis uses a founder-lifespan standard deviation of
4.0. `DEFAULTS['founder_life_sd']` is 8.0, and that is what `core.py` draws
from in real play and what this same file's own `_ingame_options` uses.

So the tool that exists to show how outcomes are distributed under mortality
is sampling a distribution half as wide as the one the game actually plays.
It will understate the tail in both directions, which is the specific thing
a sweep is for.

## Why neither was fixed here

The constants migration's rule was to move a literal into a named constant
without changing what it says, so that the diff stays behaviour-preserving
and the `perf_fingerprint` check stays meaningful. Changing 72,000 to 60,000
would change what `path` reports; changing 4.0 to 8.0 would change what
`sweep` reports. Both are corrections and both deserve their own commit, a
regression test, and a look at whether anything downstream reads them.

## Before fixing the first one

Decide which number is wrong. The obvious reading is that 72,000 is the
relic and 60,000 is correct, since 60,000 is derived in front of you from
the current 2,000 h/yr default. But `founder_hours_per_year` is data, and a
scenario could set it to something else, in which case BOTH literals are
wrong and the budget should be computed rather than typed - `hours_per_year
x expected_working_years`, read from the same place the rest of the engine
reads it.

That is the better fix and it is barely larger than the small one.
