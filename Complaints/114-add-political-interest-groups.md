# Add political interest groups created by industrialisation

**Source:** playtest findings document, LATE-008. **Status:** Feature
recommendation, roadmap-sized, substantially overlapping already-planned
architecture direction.

## The player's reasoning

Generic suspicion, eminence and state notice already provide political
pressure, but late industrialisation should create actors with genuinely
conflicting interests: landowners, merchants, industrialists, organised
workers, military, bureaucracy, clergy, urban poor and academics.
Technological and economic success should change politics, not merely raise
a scalar danger meter.

## Checked against the architecture documents

`docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md` already names this
almost exactly. Direct quotes, confirmed by reading the file: "rulers and
political actors," "political competition," "political coups," and, most
directly on point, "a new technology that makes one group extraordinarily
wealthy or militarily powerful should alter political incentives and
coalitions." That is the player's finding, already written into the
external design document this project treats as direction. `ENDOGENOUS_
COSTS_AND_DOMAINS.md` Part 3 places "Politics and governance: the state as
an organisation with a balance sheet" at Layer 6, alongside "Institutions
and law." So this is not a new idea; it is a playtest-confirmed argument for
work already on the roadmap, sequenced behind economy (Layer 3), trade
(Layer 4) and settlement (Layer 5).

## What already exists

`sim/engine/society_state_pressure.py` implements a single scalar pipeline:
`state_notice()`, gated by `household_scale()` (a weighted mix of headcount,
visible wealth and eminence, each saturating at a fixed threshold), driving
hazards like confiscation. There is no faction or coalition structure; every
political consequence in the live engine is one number crossing one
threshold. This is precisely the "scalar danger meter" the player contrasts
with distinct interest groups with their own goals.

## How this sits against CLAUDE.md

§3.1: a faction's stance (landowners resent mechanisation reducing their
labour rents, workers organise once factory employment reaches some real
density) needs to be derived from the same economic state that would drive
it in reality, not asserted as a scripted reaction to a tech-tree node
completing. §3.3: political actors are agents with their own interests and
should compete for state attention through the same mechanisms other actors
would, once `LATE-001`'s actor extraction exists.

## Size

Roadmap-sized, and this is one of the later-sequenced items even within the
already-late Layer 6 slot, because faction interests only mean something
once there are real economic winners and losers to be a faction of (real
wages, real firm profits, real land rents) - all upstream work.

## Cross-references

`docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md`'s own political-actor
language, quoted above, is the direct overlap; a future agent scoping this
should start from that document's existing entity list rather than
reinventing one. `Complaints/107` (LATE-001) and `Complaints/109` (LATE-003)
share the actor/state-balance-sheet prerequisites.
