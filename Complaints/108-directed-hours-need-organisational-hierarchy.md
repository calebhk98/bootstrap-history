# Directed hours need organisational hierarchy at scale

**Source:** playtest findings document, LATE-002. **Status:** Major
roadmap-sized feature recommendation.

## The player's reasoning

At a few thousand directed hours a year, "deputies" is a workable
abstraction. At roughly 100,000 hours a year (a scale the Rome transistor
run's own late stages approached, per the player's account of large idle
directed-hour pools), the founder is no longer directing work directly; they
are directing managers who direct foremen who direct specialists. The
player's proposed hierarchy is founder, then deputies/executives, then
managers/administrators, then foremen/principal investigators, then
workers/specialists, with each added layer creating a larger span of
control at the cost of overhead, communication loss, corruption/error risk
and slower response, mitigated by technology and institutions (accounting,
statistics, telegraph, telephone, computers) that raise effective span of
control.

## How this sits against CLAUDE.md

This is a good fit for §3.1: the current model has no organisational-
overhead mechanism at all for the founder's own directed hours (a
`directed_hours_total` figure that scales without any management
constraint), so any cap this finding proposes has to be derived from a span-
of-control mechanism, not hardcoded as "hours effectiveness drops by X% past
Y." §3.3 applies too: technologies that raise effective span of control
(telegraph, telephone, statistics, computers) should be the same production-
tree nodes already in `data/`, not a new bespoke bonus table.

## What already exists

Nothing in the live engine models organisational overhead on directed hours.
`sim/engine/labour.py` and the founder's own hour-allocation machinery treat
directed hours as a single pool with no layered structure. `docs/
architecture/HISTORICAL_SIM_ARCHITECTURE.md` lists "Organizations" (states,
armies, firms, guilds, temples, universities, religious institutions) among
its target entity types and "firm/organization budgets" among its target
mechanisms, which is the closest existing architectural hook, but neither
`ENDOGENOUS_COSTS_AND_DOMAINS.md`'s milestone table nor `STATE_OF_THE_
PROJECT.md` names a management-hierarchy or span-of-control mechanism
specifically. This is a genuinely new recommendation, not a duplicate of
already-planned work, though it depends on the same `Firm`/organisation
actor groundwork `LATE-001` (`Complaints/107`) needs.

## Size

This is a roadmap-sized system, not a fix. It needs an organisational-layer
data model (who reports to whom, what each layer's span-of-control ceiling
is), a way for technologies to raise that ceiling, and a UI change (the
player's own UX-031 finding, not filed here, already asks for better idle-
hours visibility, which this system would need too). This is naturally
sequenced after the `Firm`/actor extraction `LATE-001` needs, since a
management hierarchy inside a single founder household and a management
hierarchy that also has to account for independent firms' own staff are
closely related problems.

## Cross-references

`Complaints/107` (LATE-001, independent firms) shares the actor-extraction
prerequisite. The playtest document's own UX-031 finding (idle directed
hours, not filed as a numbered complaint here since it is UX rather than one
of this batch's nineteen) is the symptom this system would ultimately treat
as a real constraint rather than a display problem.
