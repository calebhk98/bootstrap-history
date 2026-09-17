# Architecture documents

Direction for where the simulator is going, and an honest account of where it
is now. None of this is an approved plan yet.

| File | What it is | Whose words |
|---|---|---|
| `HISTORICAL_SIM_ARCHITECTURE.md` | The target model: shared world state, stocks/flows/processes/constraints, capability frontiers, actor-owned knowledge, endogenous prices, and a testing strategy for all of it. | External design review, saved verbatim |
| `CURRENT_CODE_ARCHITECTURE_REVIEW.md` | This repository measured against that target, recommending in-place expansion over a rewrite. | External design review, saved verbatim |
| `PM_ASSESSMENT.md` | What we actually think, with the codebase measured rather than described. Agrees with most of the review, disagrees with it on five specific points, and names the requirement conflict that has to be resolved before any phase plan means anything. | Ours |

Read them in that order. `PM_ASSESSMENT.md` is the one that carries decisions;
the other two are inputs to it.

The two external documents are saved unedited so that later disagreements can
be checked against what was actually proposed. If we adopt or reject part of
them, that is recorded in `PM_ASSESSMENT.md`, not by editing them.
