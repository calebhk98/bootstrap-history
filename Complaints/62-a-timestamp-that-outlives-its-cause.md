# `restore` can charge the full price off a timestamp a manual mothball never refreshed

## What the player saw

A concern had previously closed from staffing loss. Much later it was
manually mothballed and immediately restored. `restore` claimed the concern
had been closed for many years and charged the full rebuild-style restore
cost rather than the short-closure grace discount.

## Verified against current code

Confirmed, and the exact mechanism is narrower and more precise than the
player's own hypothesis - I traced it to one missing line, not a vaguer
"conflated dictionary" problem.

All four functions the player names are in `sim/engine/projects_staffing.py`
and `sim/engine/projects_ventures.py` (moved out of the single old
`projects.py`).

`close_unstaffed_ventures()` (`projects_staffing.py:37-109`) sets the
timestamp on an automatic staffing closure:

    _sfs = getattr(self.household, "shut_for_staff", {})
    _sfs[worst] = yr
    self.household.shut_for_staff = _sfs

`open_venture()` (`projects_ventures.py:208-330`) reads it for the discount
**and clears it**, unconditionally, on every successful open:

    _shut = getattr(self.household, "shut_for_staff", {})
    if k in _shut and self.year - _shut[k] <= self.STAFF_CLOSURE_GRACE:
        fee *= self.STAFF_CLOSURE_DISCOUNT
    ...
    self.household.operating.add(k)
    self.household.mothballed.discard(k)
    _shut.pop(k, None)
    self.household.shut_for_staff = _shut

`restore_work()` (`projects_staffing.py:815-896`) reads the same dictionary
for the same discount (`_shut = getattr(self.household, "shut_for_staff", {})`,
`projects_staffing.py:848`) - but its entire body, read start to finish,
never once writes back to `shut_for_staff` or `self.household.shut_for_staff`.
No `.pop(`, no reassignment, nothing. `open_venture` clears the entry it
reads; `restore_work` does not.

`mothball_work()` (`projects_staffing.py:726-802`) never touches
`shut_for_staff` at all, confirmed by reading its full body - it moves the
node between `operating` and `mothballed` and nothing else.

Putting the sequence together, this reproduces the player's exact report:

1. A staffing closure sets `shut_for_staff[k] = year1`.
2. The concern is brought back with **`restore`**, not `open` - a
   perfectly ordinary player action, since both verbs are documented as
   ways to reopen a mothballed concern. `restore_work` correctly applies
   the grace discount (`year1` is recent) - but never clears the entry,
   because only `open_venture` does that.
3. The concern runs normally for years, or decades.
4. The player manually `mothball`s it. `mothball_work` never writes
   `shut_for_staff`, so the ancient `year1` entry is still sitting there,
   now genuinely stale relative to what the player just did.
5. The player immediately `restore`s it again. `restore_work` reads
   `_shut[k] == year1`, computes `self.year - _shut[k]` against a
   multi-year-or-decade-old timestamp, correctly finds the grace window
   (`STAFF_CLOSURE_GRACE`, declared as 6 years, `projects.py:183-194`) has
   long lapsed, and charges the full price with a message that says the
   staffing window closed years ago - which is true of the *ancient*
   staffing closure, and false of the *actual* reason the concern was shut
   moments earlier.

The bug is not that the price is numerically wrong in every case (a fresh
manual mothball, with no history, correctly gets no discount either way,
since there is nothing in `shut_for_staff` to read); it is that the
*explanation* attaches a years-old cause to a moments-old closure whenever
the concern's history includes an earlier `restore` (which never cleared the
timestamp) followed by a later manual `mothball` (which never wrote a fresh
one, or any marker of its own kind). Depending on exactly how much time
elapsed between the original staffing closure and this sequence, the same
missing clear can also produce the opposite error: a manual mothball
immediately restored *within* the original `STAFF_CLOSURE_GRACE` window
would wrongly receive the staffing discount for a closure that was not a
staffing closure at all.

Status: **confirmed in current code** - the missing clear in `restore_work`
is a direct, one-line absence, verified by reading the complete function
body rather than inferring it.

## Cross-references

No open complaint names this. `Complaints/54` and `56` (this project's own
naming-convention examples) are unrelated subjects; checked the index for
anything else touching `shut_for_staff`, `mothball`, or `restore` and found
none. This is a fresh finding.

## What would resolve it

The player's suggested fix is right and is a small change. At minimum:

- `restore_work()` should pop `_shut.pop(k, None)` after a successful
  restore, the same way `open_venture()` already does, so both verbs that
  bring a concern back leave `shut_for_staff` in the same clean state.
- `mothball_work()` arguably should not need to write `shut_for_staff` at
  all if the above is fixed, since a stale entry could then only exist
  between an original staffing closure and the *first* subsequent
  open/restore, never survive past it.

The player's larger suggestion - replace the one overloaded timestamp
dictionary with an explicit `closure_reason`/`closure_year` pair - is also
sound and is already the direction `Complaints/` itself points
(`ARCH-003` in the player's own document, and CLAUDE.md SS7's naming
discipline would want `shut_for_staff` split rather than reused for a
"pretend I don't exist" grace calculation it was never named for). It is a
bigger change than this bug needs to fix, though it would make the next
version of this exact mistake structurally harder to write, since a
`mothball_work` that had to set an explicit `closure_reason = "manual"`
could not silently leave a stale `"staff_attrition"` reason in place the way
today's shared dictionary can.

Neither fix touches CLAUDE.md SS3.5 (no save migration): `shut_for_staff` is
already a plain dict in `SAVE_FIELDS`-covered state; clearing an entry on
`restore` changes behaviour going forward within a build, not the save
format, and splitting it into a reason/year pair would be a rename this
project's own rule says needs no migration path, only within-build
round-trip correctness (which `SAVE_FIELDS`'s existing coverage already
tests for).

## The invariant

    manual mothball should not inherit stale staff-closure age

The player's own ARCH-002 phrasing. The concrete regression: staff-close a
concern -> restore it -> let years pass, well past `STAFF_CLOSURE_GRACE` ->
manually mothball it -> immediately restore it -> assert the restore uses
the manual-closure rule (full price, with no "shut N years ago" citation
against the original staffing event), not the ancient timestamp.
