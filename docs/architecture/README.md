# Architecture documents

Direction for where the simulator is going, and an honest account of where it
is now. None of this is an approved plan yet.

| File | What it is | Whose words |
|---|---|---|
| `HISTORICAL_SIM_ARCHITECTURE.md` | The target model: shared world state, stocks/flows/processes/constraints, capability frontiers, actor-owned knowledge, endogenous prices, and a testing strategy for all of it. | External design review, saved verbatim |
| `CURRENT_CODE_ARCHITECTURE_REVIEW.md` | This repository measured against that target, recommending in-place expansion over a rewrite. | External design review, saved verbatim |
| `PM_ASSESSMENT.md` | What we actually think, with the codebase measured rather than described. Agrees with most of the review, disagrees with it on five specific points, and names the requirement conflict that had to be resolved before any phase plan meant anything. | Ours |
| `ENDOGENOUS_COSTS_AND_DOMAINS.md` | The plan. How a price gets calculated rather than looked up, which domains produce prices and which only consume them, and the milestones. Supersedes `PM_ASSESSMENT.md` §3.5 and §5. | Ours |
| `HOUSEHOLD_EXTRACTION.md` | Design for moving the founder's ~80 attributes onto their own object in `sim/engine/actors/`, so a government, a firm or a second player can own things too. Includes the measured reason `__getattr__` forwarding is not an option. | Ours |
| `SIM_STATE_INVENTORY.md` | Every `Sim` instance attribute, measured, classified household / world / scenario / internal. The input to the extraction. | Ours |
| `NAMING_PLAN.md` | The 3,813 short identifiers, what they mean, and how to rename them safely. Tiered by risk. | Ours |

Read them in that order. `ENDOGENOUS_COSTS_AND_DOMAINS.md` is the live plan;
`PM_ASSESSMENT.md` is the reasoning that led to it; the two external documents
are inputs to both.

The requirement conflict `PM_ASSESSMENT.md` §4 raised has been settled with the
stakeholder: **the historical record must be a plausible outcome, not the only
one, and not one produced by feeding history back in.** The baseline is allowed
to get worse while the mechanisms that will make it good are built.

The two external documents are saved unedited so that later disagreements can
be checked against what was actually proposed. If we adopt or reject part of
them, that is recorded in `PM_ASSESSMENT.md`, not by editing them.
