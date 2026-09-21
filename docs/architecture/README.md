# Architecture documents

Direction for where the simulator is going, and an honest account of where it
is now. None of this is an approved plan yet.

| File | What it is | Whose words |
|---|---|---|
| `HISTORICAL_SIM_ARCHITECTURE.md` | The target model: shared world state, stocks/flows/processes/constraints, capability frontiers, actor-owned knowledge, endogenous prices, and a testing strategy for all of it. | External design review, saved verbatim |
| `CURRENT_CODE_ARCHITECTURE_REVIEW.md` | This repository measured against that target, recommending in-place expansion over a rewrite. | External design review, saved verbatim |
| `PM_ASSESSMENT.md` | What we actually think, with the codebase measured rather than described. Agrees with most of the review, disagrees with it on five specific points, and names the requirement conflict that had to be resolved before any phase plan meant anything. | Ours |
| `ENDOGENOUS_COSTS_AND_DOMAINS.md` | The plan. How a price gets calculated rather than looked up, which domains produce prices and which only consume them, and the milestones. Supersedes `PM_ASSESSMENT.md` §3.5 and §5. | Ours |
| `PRICES_JSON_DELETION.md` | The deletion contract, remaining readers and ordered work required to remove `data/prices.json` rather than preserve or rename it. | Ours |
| `HOUSEHOLD_EXTRACTION.md` | Design for moving the founder's ~80 attributes onto their own object in `sim/engine/actors/`, so a government, a firm or a second player can own things too. Includes the measured reason `__getattr__` forwarding is not an option. | Ours |
| `SIM_STATE_INVENTORY.md` | Every `Sim` instance attribute, measured, classified household / world / scenario / internal. The input to the extraction. | Ours |
| `NAMING_PLAN.md` | The 3,813 short identifiers, what they mean, and how to rename them safely. Tiered by risk. | Ours |
| `STATE_OF_THE_PROJECT.md` | Every `Complaints/` file and every milestone in `ENDOGENOUS_COSTS_AND_DOMAINS.md`, checked against the current code rather than against what was last said about it. | Ours |
| `SIM_DECOMPOSITION_REVISITED.md` | Reopens, on the stakeholder's request, the "no full decomposition" decision in `sim/ARCHITECTURE.md`; checks which of that decision's reasons still hold and recommends a staged, partial alternative. | Ours |
| `WIRING_MILESTONE_4.md` | What wiring demography and agriculture into the engine actually broke and fixed, commit by commit. Feeds Milestone 4 in `STATE_OF_THE_PROJECT.md`. | Ours |
| `DEMAND_AT_SCALE.md` | Whether `sim/world/demand.py`'s household-demand model holds outside Roman Egypt, against the stakeholder's own critique. | Ours |
| `MAP_AND_WEATHER.md` | Why the map and the weather model are two disconnected systems, and what it would take to join them. | Ours |

Read them in that order. `ENDOGENOUS_COSTS_AND_DOMAINS.md` is the live plan and
`PRICES_JSON_DELETION.md` is its concrete exit checklist for the legacy file;
`PM_ASSESSMENT.md` is the reasoning that led to it; `STATE_OF_THE_PROJECT.md`
is where its milestone table is kept current; the two external documents
are inputs to all of them.

The requirement conflict `PM_ASSESSMENT.md` §4 raised has been settled with the
stakeholder: **the historical record must be a plausible outcome, not the only
one, and not one produced by feeding history back in.** The baseline is allowed
to get worse while the mechanisms that will make it good are built.

The two external documents are saved unedited so that later disagreements can
be checked against what was actually proposed. If we adopt or reject part of
them, that is recorded in `PM_ASSESSMENT.md`, not by editing them.
