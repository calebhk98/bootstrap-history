# Add cross-system invariant tests, not only local ones

**Source:** playtest findings document, ARCH-002. **Status:** Architecture/
testing recommendation. High value; overlaps directly with several bugs
another agent is filing in this same review round.

## The player's reasoning

Most serious playtest failures occurred at the boundary between two
individually reasonable systems, not inside either one. Their proposed
invariant list, verbatim from the document:

    local town population <= national population
    reachable trade population <= physically possible national pool
      (except explicitly founder-trained people, still bounded by household headcount)
    if a number is called a ceiling: current value <= ceiling
    quoted affordable purchase should succeed if state is unchanged
    displayed annual resource surplus should not simultaneously be an unexplained throttle
    auto-investment should include active + pending capacity
    event human losses <= source population
    fog-mode response contains no undiscovered ID anywhere
    manual mothball should not inherit stale staff-closure age
    goal-metric delta should equal the effects reported in state after the turn

## Why this belongs as its own complaint rather than folded into a bug report

Each invariant above corresponds to a specific bug the player found and
reported in section 1 of the same document; those bugs are in the number
range another agent is filing this round (`Complaints/58` through
`Complaints/102`, per the reserved ranges in this review). This complaint's
job is narrower and more durable than any one of those bug fixes: propose
the invariant as a standing, generic test that would have caught the bug
class, not just the one instance, and would keep catching regressions after
the specific bug is fixed.

## Mapping invariants to the bugs that motivated them

Matched against the playtest document's own bug numbering (BUG-001 through
BUG-008, SUSPECT-010/011, REVIEW-012, BUG/INVARIANT-013):

- `local town population <= national population` and `reachable trade
  population <= physically possible national pool` - BUG-001 (local labour
  market larger than the surviving civilisation).
- `if a number is called a ceiling: current value <= ceiling` - BUG-007
  (elite literacy exceeding its own reported ceiling).
- `quoted affordable purchase should succeed if state is unchanged` -
  BUG-004 (forest quote counts credit, purchase does not).
- `displayed annual resource surplus should not simultaneously be an
  unexplained throttle` - SUSPECT-010 (charcoal shown as both surplus and
  the active bottleneck).
- `auto-investment should include active + pending capacity` - BUG-008
  (auto-mine ignores mine capacity already under construction).
- `event human losses <= source population` - BUG/INVARIANT-013 (event text
  describing tens of thousands affected after population had collapsed to
  the low hundreds).
- `fog-mode response contains no undiscovered ID anywhere` - BUG-006 (fog
  scrubbing leaking hidden IDs and producing malformed partial-ID text).
- `manual mothball should not inherit stale staff-closure age` - BUG-005
  (`shut_for_staff` retaining a stale closure year).
- `goal-metric delta should equal the effects reported in state after the
  turn` - not tied to one numbered bug in this document; it is closest to
  UX-015's "show goal-relevant deltas on completion" recommendation, which
  is a UX finding rather than a bug, so this invariant is partly aspirational
  (a real check that the reported delta and the live-state delta agree)
  rather than purely a regression guard for an existing defect.

## How this sits against CLAUDE.md

§6 already states the project's own hard lesson on exactly this class of
problem: "green tests do not mean unchanged behaviour... the suite asserts
on outputs and messages, not on the simulation being the same simulation."
Cross-system invariants are a different and complementary kind of test from
both the message-level regression suite and `perf_fingerprint.py`'s byte-
identical behaviour proof: they check a relationship between two subsystems'
outputs that neither subsystem's own local tests can see, which is exactly
the gap CLAUDE.md's own traps section describes for the `id()`/cache bug
(`Complaints/27`, closed) - that bug, too, was only visible at the boundary
between two systems (a cache and the allocator), not inside either one.

## Size

Medium, and incremental: each invariant above can be written as an
independent test function once its corresponding bug fix lands (several are
in the other agent's `Complaints/58`-`102` range and not yet fixed as of
this writing), so this is naturally a rolling addition to `sim/tests/`
rather than one commit.

## Cross-references

`Complaints/58` through `Complaints/102` (this review round's bug-report
range, filed by a separate agent) contain the specific instances; this
complaint is the standing-invariant version of the same list. `ARCH-003`
(`Complaints/121`) is the specific fix `shut_for_staff`'s invariant above
depends on.
