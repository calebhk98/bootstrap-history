# review/ - the audit trail

Kept because the provenance of a correction matters as much as the correction.

| File | What it is |
|---|---|
| `INDEPENDENT_AUDIT.md` | A hostile reviewer's report on a random sample of 70 nodes, each judged in isolation, plus the author's RESOLUTION recording what was done about every finding. **This is the only trustworthy measurement of the tree's error rate.** It found 37 of 70 defective, and found that 8 of 8 nodes carrying an automated repair tag were wrong. |
| `AUDIT_SAMPLE.json` / `.txt` | The 70 nodes that were sampled, with prerequisite names resolved, exactly as the reviewer saw them. |
| `caps_batch_0..4.json` | The 318 nodes found to be missing a capability prerequisite, split five ways. |
| `caps_fix_0..4.json` | What five reviewers decided about each of those 318, one node at a time, with a one-line reason each. Note how often the answer is an empty list: 417 of the decisions were "this genuinely needs no capability rung", which is the answer a keyword heuristic can never give. |
| `SHALLOW_NODES.txt` | Nodes flagged as narrow at the top and shallow all the way down. |
| `DOCS_VS_ENGINE.md` | A documentation audit: statements in the project's own prose (`ROME_BOOTSTRAP.md`, `COMMODITIES.md`, the knowledge corpus, the design notes) that describe a mechanic the engine does not implement, verified against the code, ranked by how much building it would add. |
| `MATERIAL_GATING.md` | Every one of the 162 material keys checked for the rubber bug (`ac69bfb`): a consumer with no route in its own ancestry to a node that can produce the material, still sold it at a flat book price anyway. Found the same bug recurring in 24 materials (84 consumer nodes: aluminium, sulfuric acid, nickel, tungsten, platinum, porcelain, ...), fixed all 24, and separately judged 138 materials genuinely purchasable without personal production (iron, copper, wool and 136 more like them) and 3 (including the goal node's own `indium_g`) as needing a production node that does not exist yet. |

## The short version of what happened here

1. An automated pass inferred 112 missing capability prerequisites from keywords
   in each node's prose. The project's own audit score rose from 80.8 to 98.0.
2. An independent reviewer sampled 70 nodes and found that **every one of the
   eight carrying an inferred prerequisite was wrong.**
3. All 112 were reverted, tree-wide. Inference is now off by default. The score
   fell to 93.1, which was the honest number all along.
4. The 318 real gaps were handed to reviewers to decide one at a time, with the
   observed failure modes written into their brief. They added 86 edges and
   judged 417 decisions to need nothing.

**The lesson, which is the reason this directory exists:** a checker that
grades work its own repair script produced will report whatever that script was
built to satisfy. The number went up and the tree got worse.
