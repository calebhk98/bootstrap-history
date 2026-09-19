# Prefer explicit state causes over overloaded flags

**Source:** playtest findings document, ARCH-003. **Status:** Architecture
recommendation, illustrated by a specific bug filed elsewhere in this
review round.

## The player's reasoning

`shut_for_staff` illustrates the problem directly: one dictionary
simultaneously indicates cause, timing, restore-discount eligibility and
auto-reopen eligibility. As lifecycle complexity grows, explicit state is
safer: separate `closure_reason`, `closure_year`, `restore_rule` and
`auto_reopen_allowed` fields rather than one overloaded timestamp dictionary
carrying all four meanings. The player notes the same principle may help
mines, institutions, hazards and project resets, which currently show
similar patterns (a single flag or timestamp made to answer more than one
question).

## The concrete bug this is illustrated by

The playtest document's own BUG-005 (section 1) describes exactly this
failure mode in `shut_for_staff`: a concern closed once from staffing loss,
then much later manually mothballed and immediately restored, was charged
the full rebuild-style restore cost because `mothball_work()` does not clear
a stale `shut_for_staff` timestamp and `restore_work()` reads that
timestamp to determine the grace period. This is the same bug another agent
in this review round is filing as a defect (in the `Complaints/58`-`102`
range, referenced there as complaint 62 per the assigned overlap in this
task's own brief). This complaint is the architectural generalisation of
that specific bug, not a duplicate of it: fixing the one stale-timestamp
case closes the bug; adopting explicit state fields for closure/restore
lifecycle prevents the whole class from recurring in mines, institutions,
hazards and project resets, which the player explicitly calls out as
carrying the same risk shape.

## How this sits against CLAUDE.md

This is a code-hygiene finding rather than a §3.1/§3.2 one, but it connects
to §6's "traps that have already bitten someone" in spirit: an overloaded
flag is the same category of hazard as the `id()`-keyed cache bug
(`Complaints/27`, closed) in one respect - both are cases where one piece of
state is asked to mean two different things depending on which code path
reads it, and the collision is invisible from inside either reading path.
`sim/world/deposits.py`'s `working_life_years` parameter, documented in
`Complaints/56` (open, "A shaft that costs nothing to sink"), is a second,
independent instance of the exact same shape: one number resolved in two
places with two different meanings (an amortisation horizon in one function,
a physical reserve size in another), discovered by a different agent
working on a completely different subsystem. Three independent instances of
the same defect shape (shut_for_staff, the id()-cache bug, and deposits.py's
working_life_years) is reasonable evidence this is a recurring failure mode
in this codebase specifically, not a one-off.

## Size

Small per instance (adding explicit fields to replace one overloaded flag
is a contained, mechanical change once the fields are named), but the
player's own scope note - "the same principle may help mines, institutions,
hazards and project resets" - means a full sweep across those four areas is
a medium-sized, multi-file cleanup, not a single fix. Treat the
`shut_for_staff` case as the first instance to fix (already filed as a bug
elsewhere) and this complaint as the standing principle to apply the next
time a similar overloaded flag is found, rather than a single ticket to
close in one pass.

## Cross-references

The `shut_for_staff` bug itself is filed in the other agent's number range
(`Complaints/58`-`102`, referenced there as complaint 62 per this review's
own cross-reference). `Complaints/56` (open, "A shaft that costs nothing to
sink") documents the `working_life_years` instance of the same pattern.
`Complaints/120` (ARCH-002) lists "manual mothball should not inherit stale
staff-closure age" as one of its proposed invariants, which is the
regression-test half of what this complaint asks for architecturally.
