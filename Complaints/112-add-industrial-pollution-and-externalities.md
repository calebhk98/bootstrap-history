# Add industrial pollution and externalities

**Source:** playtest findings document, LATE-006. **Status:** Feature
recommendation, medium size, not currently named in the architecture
documents.

## The player's reasoning

A coal, smelter or chemical industrial revolution should eventually damage
air, water, soil, urban health and agricultural land. Without this, early
sanitation technology permanently solves disease while industry scales
without any offsetting side effect. Possible mechanisms the player names:
smoke mortality, contaminated rivers, mine runoff, occupational disease,
noise/fire risk, and cleanup/regulation technology as a later counter-move.

## Checked against the architecture documents

Searched `docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md` and `CURRENT_
CODE_ARCHITECTURE_REVIEW.md` directly for "pollution" and "externalit[y]":
no matches in either. This is not currently on the architecture roadmap in
any form; it is a genuinely new recommendation.

## What already exists

`sim/engine/society_hazards.py` (the `HazardsMixin`) already models disease
burden, mortality and household mitigation as distinct mechanisms, and
`sim/world/demography.py` carries a nutrition-linked mortality path wired
into `_demographic_recovery`. There is no channel today by which industrial
activity itself (mining output, smelting throughput, coal consumption)
feeds back into mortality or land productivity. This would be a genuinely
new coupling: industrial output on one side, an occupational/environmental
mortality or agricultural-yield penalty on the other, both derived from
physical throughput (tonnes of ore smelted, coal burned) rather than
asserted as a flat "industry is now X% worse for health."

## How this sits against CLAUDE.md

§3.1 governs the mechanism the same way it governs everything else on this
list: smoke mortality or mine runoff has to scale with an actual measured
quantity (tonnes of coal burned, tonnes of ore processed near a settlement)
rather than a flat penalty applied once a civilisation crosses some
industrialisation threshold. §3.3 is satisfied automatically if built this
way: pollution becomes a normal consequence of existing production and
mining flows, not a bespoke "industrial revolution now hurts you" branch.

## Size

Medium, smaller than most of the other LATE findings, because it can attach
to existing production/mining throughput numbers (`data/production/`'s own
recipes already record material flows) rather than needing a wholly new
subsystem like firms or urbanisation. It is still a real feature, not a
one-line fix: it needs a mortality or yield-penalty function derived from
throughput, and ideally a later mitigation technology path (regulation,
scrubbers, water treatment) for the player to build toward.

## Cross-references

None found in `docs/architecture/` or the open complaints list; this is a
standalone new finding with no overlap to flag.
