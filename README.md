# How this project is put together

Three artefacts that share one dataset. This checkout does not have to be
named anything in particular; every command below is written relative to the
repository root, whatever you called the directory when you cloned it.

```
00_BRIEFING.md            your first thousand days
01_WORLD_STATE_100AD.md   what Rome has and lacks, materials, prices, mindset
02_STRATEGY.md            the plan, the phases, and the evidence for them
03_SOCIAL_POLITICS.md     patronage, law, what the State funds, what kills you
04_ECONOMICS.md           labour, materials, transport, where the money goes
LABOR_LEDGER.md           the founder's hours, and the author's
knowledge/                THE HOW-TO LIBRARY (start at 00_NONOBVIOUS_TRICKS.md)
data/
├── tech_tree.json        the tech tree, fully costed (node and edge counts below)
├── branches/             per-domain source files, CONTRACT and VOCABULARY
├── judgement.json        per-node scores and defects (generated)
└── prices.json           wages and commodity prices, confidence-tagged
sim/
├── treetool.py           merge / repair / JUDGE EACH TECH IN ISOLATION
├── simulator.py          validate / path / costs / run / compare / sensitivity / play
└── strategies/*.json     rush, and the recommended order, with reasoning
log/playthrough_01.md     real traces: lucky, typical, and failed
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

and `knowledge/10_metallurgy.md` contains a `### zinc_metal` entry with the
actual procedure: ore, ratios, temperatures, vessel, condenser design, what
success looks like, how it fails, what it costs, and what it will do to your
lungs. **That link is the point of the whole project.** A tech tree that says
"microscope requires glass" is useless to someone who does not already know that
a single melted bead of glass gives 250x. The tree tells you *what* and *in what
order*; the library tells you *how*, at a level of detail a competent
non-specialist can actually act on.


## The three layers, and why the tree is built this way

The tree is built in three layers so that a reader can see WHY something is
hard, not just that it is: "grind a lens" requires "hold one micron", and
"smelt zinc" requires "reach 1000 C", as explicit prerequisites rather than
implicit difficulty.

**1. CAPABILITY RUNGS (34 nodes, `cap_*`).** Graded, explicit, and cited as
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

**2. MATERIALS (74 nodes, `mat_*`).** Each is a node with its own prerequisites,
not a line item with a price. Rome's starting materials are granted explicitly
by its civilization profile. **There is no "unobtainable" bucket**: rubber is
not unobtainable, it is in West Africa; saltpetre effloresces on the Gangetic
plain, on a route Rome already sails. `mat_natural_rubber`, `mat_gutta_percha`,
`mat_quinine`, `mat_chile_nitrate`, `mat_newworld_crops`, `mat_cryolite` and
`mat_platinum_bulk` are each gated behind an `exp_*`
expedition node that prices what going to get it actually costs, exactly like
every other distant material (see `knowledge/95_expeditions.md`).

**3. TECHNOLOGIES (everything that is not a capability rung or a material).**
Textiles, food and agriculture, household goods, media and printing, land
transport, ships, aviation, energy, chemicals, metallurgy and mining,
precision and machine tools, medicine, civil engineering, optics and
instruments, communications and computing, on top of the core spine - branch
authors add categories as they add branches, so this list is not exhaustive.
The exact split between layers moves as branches are added; count it yourself
rather than trust a number here:

```bash
python3 -c "import json,collections
nodes = json.load(open('data/tech_tree.json'))['nodes']
prefix = collections.Counter(n['id'].split('_')[0] if n['id'].startswith(('cap_','mat_')) else 'tech' for n in nodes)
print('cap_*:', prefix['cap'], ' mat_*:', prefix['mat'], ' everything else:', prefix['tech'])"
```

**Scale:** 2,864 nodes and 5,025 edges as of this writing, confirmed by
`python3 sim/simulator.py validate`, which prints both on every run.
Availability and ordering come from the prerequisite graph, costs, capability
rungs, and civilization starting knowledge. The transistor
(`junction_transistor`, the 1951 device) needs 169 of those nodes, itself
included (`python3 sim/simulator.py path junction_transistor`, which lists
them and stops there). Most of the tree has nothing to do with a transistor,
and that is the point: a tree that only covers the path to a transistor is
dishonest about what technology is for.

## Judging each technology in isolation

The right test is not "what year does the simulation reach a transistor". It is
**"could someone holding exactly this node's prerequisites, and nothing else,
actually build it?"** That is what `treetool.py judge` asks, node by node.

```bash
# judge, judge --full and judge --grade can write data/judgement.json, but
# only with --write; without it they report and change nothing. judge --id
# never writes - it reports on one node and stops.
python3 sim/treetool.py judge                        # score every node, summary
python3 sim/treetool.py judge --full                 # every defect, node by node
python3 sim/treetool.py judge --id zinc_metal        # one report card
python3 sim/treetool.py judge --grade C              # everything at C or worse
```

Defect classes it names: `CAP-NONE` and `CAP-HEAT`/`CAP-TOL`/`CAP-VAC`/
`CAP-PURITY`/`CAP-POWER` (needs a capability rung it does not declare),
`SHALLOW` (narrow at the top and shallow all the way down), `BLOCKED`
(depends on something marked unobtainable - currently dormant, since nothing
in the tree is marked that way any more), `COST-HIGH` / `HOURS-HIGH` /
`HOURS-ZERO` (out of proportion for its category or graph position),
`NO-FLOOR` (long adoption with no diffusion time), `NOTE-THIN`, `NO-CONF`,
`NO-RECIPE`, `SOCIAL-FLAT`. The full, current list is the `defects.append(...)`
calls in `sim/treetool.py`'s `judge_node`; treat the list above as a reading
aid, not the authority.

**Read the score with suspicion.** As of this writing `judge`
reports a mean of 96.0/100 across all nodes (2,294 A, 473 B, 93 C, 4 D, 0 F -
rerun the command above for the current figures). `treetool.py repair`
does not guess at capability prerequisites: it leaves
gaps visible for a human to review rather than inferring them, because an
earlier version of this same pass inferred capability floors and an
independent reviewer who checked a sample of its output by hand found every
one of them wrong. That reviewer's findings are in
`data/review/INDEPENDENT_AUDIT.md`, a random sample of 70 nodes checked
without seeing the tree's own heuristics, and it is the more trustworthy
read of tree quality than the score above. 398 nodes still carry a
`[AUDIT: capability prerequisite(s) ... were inferred ... Treat them as a
floor, not a specification.]` marker in their `_internal` field from before
that inference was turned off (`python3 -c "import json; nodes=json.load(open('data/tech_tree.json'))['nodes']; print(sum(1 for n in nodes if 'AUDIT' in str(n.get('_internal',''))))"`
counts them); `_internal` is for auditors, not players - `note` is what a
player reads, and these markers once lived there instead, which is how a
first-time tester found one inside the win condition itself.

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
| `ph` | **Your own hours.** The scarce resource. Total available in one lifetime, printed by `python3 sim/simulator.py path <any node>` as "Founder-hours available in one lifetime" (currently 56,000). |
| `lab` | Hired hours by trade, priced from `prices.json` |
| `yrs` | **Calendar floor.** Curing, growing, maturing, or a generation of economic diffusion. Money cannot buy this down; `python3 sim/simulator.py path junction_transistor` shows what floor a given goal adds up to (currently 142.2 years for the transistor). |
| `risk` | Probability an attempt fails outright and must be retried at 40% of cost |
| `sus` | Suspicion delta. Rome executes magicians and your chemistry looks like magic. |
| `gov` | State interest, -3 (will suppress) to +3 (will fund and demand) |
| `sch` / `art` | Trained people required. This is what the greedy strategy runs out of. |
| `conf` | A well attested, B probable, C the author's estimate |

`sus` and `gov` are contested. Both are present on all nodes and are still
read (see `sim/engine/cli.py`'s `why` display), but `data/branches/CONTRACT_V2.md`
§4 is the place to check before relying on them further - it carries the
authors' current view of where these two fields are headed, and that view
is more likely to move than this table is to be updated in step with it.

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
