# rome/ - how this project is put together

Three artefacts that share one dataset.

```
rome/
├── 00_BRIEFING.md            your first thousand days
├── 01_WORLD_STATE_100AD.md   what Rome has and lacks, materials, prices, mindset
├── 02_STRATEGY.md            the plan, the phases, and the evidence for them
├── 03_SOCIAL_POLITICS.md     patronage, law, what the State funds, what kills you
├── 04_ECONOMICS.md           labour, materials, transport, where the money goes
├── LABOR_LEDGER.md           the founder's hours, and the author's
├── knowledge/                THE HOW-TO LIBRARY (start at 00_NONOBVIOUS_TRICKS.md)
├── data/
│   ├── tech_tree.json        2,833 nodes, 4,745 edges, fully costed
│   ├── branches/            per-domain source files, CONTRACT and VOCABULARY
│   ├── judgement.json       per-node scores and defects (generated)
│   └── prices.json           wages and commodity prices, confidence-tagged
├── sim/
│   ├── treetool.py           merge / repair / JUDGE EACH TECH IN ISOLATION
│   ├── simulator.py          validate / path / costs / run / compare / sensitivity / play
│   └── strategies/*.json     rush, and the recommended order, with reasoning
└── log/playthrough_01.md     real traces: lucky, typical, and failed
```

## The one rule that keeps it coherent

**Every claim about cost, time or dependency lives in `data/`. Every claim about
how to physically do something lives in `knowledge/`. Prose files quote the data,
they never assert it.** Every number in `02_STRATEGY.md` and `04_ECONOMICS.md`
was computed by the simulator from the data files, so if you edit the tree, run
the commands again and the documents are wrong until you do.

## The link between the tree and the library

Every node in `tech_tree.json` carries a `kb` field pointing at a file and an
anchor, for example:

```json
"id": "zinc_metal",
"kb": "10_metallurgy.md#zinc_metal",
```

and `rome/knowledge/10_metallurgy.md` contains a `### zinc_metal` entry with the
actual procedure: ore, ratios, temperatures, vessel, condenser design, what
success looks like, how it fails, what it costs, and what it will do to your
lungs. **That link is the point of the whole project.** A tech tree that says
"microscope requires glass" is useless to someone who does not already know that
a single melted bead of glass gives 250x. The tree tells you *what* and *in what
order*; the library tells you *how*, at a level of detail a competent
non-specialist can actually act on.


## The three layers, and why the tree is built this way

The first version of this tree had 128 nodes and treated materials as priced
commodities and capabilities as things you either had or did not. That was the
central flaw: "grind a lens" did not require "hold one micron", and "smelt zinc"
did not require "reach 1000 C", so a reader could not see WHY anything was hard.
The rebuild has three layers.

**1. CAPABILITY RUNGS (33 nodes, `cap_*`).** Graded, explicit, and cited as
prerequisites by the technologies that need them. These are the answer to
"did you account for accuracy, furnaces, purity?".

| Ladder | Rungs |
|---|---|
| Furnace temperature | 700 C (Rome has it) - 1100 (hand bellows, Rome has it) - 1300 (water blast, cast iron) - 1600 (regenerative) - 2000 (oxy-hydrogen) - 3000 (electric arc) |
| Machining tolerance | 1 mm (Rome has it) - 0.1 mm - 0.01 mm - 1 micron - 0.1 micron |
| Vacuum | 1 torr - 1e-3 - 1e-6 - 1e-9 |
| Purity | 99% - 99.99% - 99.9999% - 1 part in 1e9 |
| Power | muscle - water (Rome has it) - steam - local electric - grid |
| Measurement | length, mass to 1 mg, temperature, high temperature, time to 1 s, to 1 ms, absolute electrical units, wavelength |

**2. MATERIALS (73 nodes, `mat_*`).** Each is a node with its own prerequisites,
not a line item with a price. Tier 0 means Rome already produces it and it is
free. **There is no longer a tier-9 "unobtainable" bucket** - that category
existed in an earlier version of the tree and it was wrong: rubber is not
unobtainable, it is in West Africa; saltpetre effloresces on the Gangetic plain,
on a route Rome already sails. `mat_natural_rubber`, `mat_gutta_percha`,
`mat_quinine`, `mat_chile_nitrate`, `mat_newworld_crops`, `mat_cryolite` and
`mat_platinum_bulk` all now sit at tier 4, each gated behind an `exp_*`
expedition node that prices what going to get it actually costs, exactly like
every other distant material (see `rome/knowledge/95_expeditions.md`).

**3. TECHNOLOGIES (2,727 nodes).** What were fifteen domains at the tree's
last major rebuild have since fragmented into 241 categories as branch authors
added their own - textiles, food and agriculture, household goods, media and
printing, land transport, ships, aviation, energy, chemicals, metallurgy and
mining, precision and machine tools, medicine, civil engineering, optics and
instruments, communications and computing remain the broad shape, on top of
the original core spine.

**Scale:** 2,833 nodes, 4,745 edges. Tier 0 (Rome already has it) 276, tier 1
607, tier 2 915, tier 3 645, tier 4 309, tier 5 81.
**The transistor (`junction_transistor`, the 1951 device) needs 158 of them.
The other 2,675 are the rest of technology, and that is the point:** a tree
that only covers the path to a transistor is dishonest about what technology
is for.

## Judging each technology in isolation

The right test is not "what year does the simulation reach a transistor". It is
**"could someone holding exactly this node's prerequisites, and nothing else,
actually build it?"** That is what `treetool.py judge` asks, node by node.

```bash
python3 rome/sim/treetool.py judge              # score all 2,833, summary
python3 rome/sim/treetool.py judge --full       # every defect, node by node
python3 rome/sim/treetool.py judge --id zinc_metal   # one report card
python3 rome/sim/treetool.py judge --grade C    # everything at C or worse
```

Defect classes it names: `CAP-NONE` and `CAP-HEAT/TOL/VAC/PURITY/POWER` (needs a
capability rung it does not declare), `SHALLOW` and `THIN-CHAIN` (narrow at the
top AND shallow all the way down), `BLOCKED` (depends on something
unobtainable), `COST-HIGH` / `COST-LOW` / `HOURS-ZERO` (out of proportion for its
tier), `NO-FLOOR` (heavy technology with no diffusion time), `NOTE-THIN`,
`NO-RECIPE`, `SOCIAL-FLAT`.

**Read the score with suspicion.** `treetool.py repair` then fixes mechanically
what it can, and the mean score rises from 80.8 to 98.0. A large part of that is
my own checker being satisfied by my own repair, which is exactly the trap this
project is supposed to avoid. Every edge the repair inferred is stamped into the
node's `_internal` field as `[AUDIT: capability prerequisite(s) ... were
inferred ... Treat them as a floor, not a specification.]`, so you can find and
discount all 398 of them. `_internal` is read by nothing in `rome/sim/engine`,
which is the point: these markers once lived in `note`, the field a player
reads, and a first-time tester found one in the win condition itself. The trustworthy check is `data/review/INDEPENDENT_AUDIT.md`, where a separate
reviewer went through a random sample of 70 nodes without seeing my heuristics.

## Simulator changes

- **Immortality is the default.** A mortality lottery that ended one run in five
  drowned the signal from the technology in noise about how long one man happened
  to live. `--mortal` turns death back on; `sweep mortality` sweeps the lifespan.
- **Reputation** is now a tracked resource, distinct from money and from
  political protection. It is your ability to be believed and followed. It
  shortens diffusion floors (people adopt faster from someone credible), attracts
  staff and patrons you did not pay for, raises State funding, and makes you
  harder to accuse. Visible, useful, State-approved work builds it; obscure
  laboratory work does not, however important, which is an annoying and real fact
  about how credibility accrues.

## Node schema

Documented in full in `data/tech_tree.json` under `meta.schema`. The fields that
matter most:

| Field | Meaning |
|---|---|
| `ph` | **Your own hours.** The scarce resource. You have about 72,000, ever. |
| `lab` | Hired hours by trade, priced from `prices.json` |
| `yrs` | **Calendar floor.** Curing, growing, maturing, or a generation of economic diffusion. Money cannot buy this down, and this is what sets the 142-year critical path. |
| `risk` | Probability an attempt fails outright and must be retried at 40% of cost |
| `sus` | Suspicion delta. Rome executes magicians and your chemistry looks like magic. |
| `gov` | State interest, -3 (will suppress) to +3 (will fund and demand) |
| `sch` / `art` | Trained people required. This is what the greedy strategy runs out of. |
| `conf` | A well attested, B probable, C the author's estimate |

## Confidence, stated plainly

- **Dependency structure: strong.** It is checkable against the history of
  technology, and `validate` proves it is an acyclic, fully priced, reachable graph.
- **Calendar floors: reasonable.** Grounded in real historical durations.
- **Costs in denarii: weak.** Bulk Roman commodity prices are reconstructed from
  the Edict of Diocletian, which is 301 AD and denominated in a collapsed
  currency, so it is used for *ratios* anchored to silver. Every such figure is
  tagged `[C]`.
- **Revenue: weakest.** These are guesses at the profit of enterprises that did
  not exist, in a market reconstructed from secondary scholarship.
- **The social model: under-powered, and I know it.** See `02_STRATEGY.md` §5.

## Editing it

```bash
python3 sim/simulator.py validate    # run this after EVERY edit to data/
```

`validate` checks acyclicity, dangling prerequisites, unpriced materials,
unknown trades, out-of-range risks, and reachability of the goal. It has caught
every mistake I made while building this, which was several.
