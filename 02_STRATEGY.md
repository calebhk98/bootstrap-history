# 02 - Master Strategy

The plan, why it is shaped this way, and the evidence from the simulator that it
is better than the obvious alternatives.

**A caveat before the numbers below: most of them are stale.** This file's
Monte Carlo figures (sections 1, 2, 3, 3b) were measured against a 1,176-node
tree with `point_contact_transistor` as the goal. The tree has since grown to
2,833 nodes and the goal moved to `junction_transistor` (see
`ROME_BOOTSTRAP.md`'s "The answer, in eight lines" for the current headline
numbers, which were re-measured after both changes). Re-running these specific
sweeps at the game's current scale is expensive and was out of scope for the
pass that added this note; what follows is the qualitative shape of the
strategy - which phase matters when, why politics rather than physics kills
runs, why more money does not simply help - which is the part of this
document least likely to have changed even though its exact percentages have.
The two numbers in section 3a that come from a deterministic graph walk
(`validate`/`path`, not Monte Carlo) have been corrected to the current tree.

Run the evidence yourself:

```
python3 rome/sim/simulator.py compare      --mc 500
python3 rome/sim/simulator.py sensitivity  --mc 300
python3 rome/sim/simulator.py path
```

---

## 1. The result, up front

150 Monte Carlo runs per strategy on the 1,176-node tree, 500-year horizon, all
three dated catastrophes active, **founder immortal** (the default: a run should
measure the tree, not a lifespan lottery).

| Strategy | Reaches the transistor | Median year | Elapsed | Dominant failure |
|---|---|---|---|---|
| **RUSH** (beeline at the goal, skip revenue, institutions, defence) | 68% | 360 AD | 260 yr | denounced as a magician, 32% |
| **TOPO** (bare topological order) | 65% | 306 AD | 206 yr | denounced as a magician, 35% |
| **RECOMMENDED** | **87%** | **275 AD** | **175 yr** | denounced as a magician, 13% |

Turning mortality back on (`--mortal`) changes almost nothing: 90%, median 276
AD. **The programme now survives its founder**, which it could not in the
128-node version, because the staff, reputation and institution mechanics carry
it. Irreducible serial calendar time on the critical path: **141 years across 28
nodes.**

## 2. The failure mode has moved, and that is the interesting result

In the first version of this project the dominant failure was succession: the
founder died before training anyone, in one run in five. That is now nearly
gone.

**What kills runs now is politics.** Between 13% and 35% of runs end with the
founder denounced as a magician, and the rate scales with how fast the strategy
moves. The greedy strategies are not punished for being technically wrong any
more; they are punished for being conspicuous. An immortal who never stops
producing marvels accumulates suspicion faster than any patron can absorb it.

This is why `RUSH` reaches 68% and still takes 85 years longer than
`RECOMMENDED`: it gets there, eventually, having spent decades rebuilding after
each seizure.

The old finding still holds and is now sharper. **The technical dependency graph
is not the real dependency graph.** The transistor needed 97 of the 1,176 nodes
this section was measured against; on the current, larger tree it needs 158 of
2,833 (see section 3a) - and in neither version is a patron, a citizenship, a
school or a licensed collegium among them. Nothing in physics requires them.
Nothing can be built without them.

## 2a. How each technology is judged, and what that found

The end date is the wrong test, so it is not the test. Each node is scored on
its own: *could someone holding exactly this node's prerequisites, and nothing
else, actually build it?*

`python3 rome/sim/treetool.py judge` reported a mean of **93.1/100** across the
1,176-node tree at the time this was written, with 260 nodes not declaring a
capability rung they need. Re-run today against the current 2,833-node tree,
the honest score is **97.0/100**, with 192 nodes still missing a capability
rung.

**Do not take that number at face value, and here is why.** An earlier version
of the repair script inferred missing capability prerequisites by matching
keywords against each node's prose, which raised the mean to 98.0. An
independent reviewer then sampled 70 nodes and found that **of the eight
carrying an inferred prerequisite, all eight were wrong**: a 1300 C blast
furnace rung on a room-temperature explosives mix, a 1600 C furnace on a
paperwork node about binary arithmetic, a vacuum rung on mercury extraction,
which reverses the dependency, because mercury is what makes vacuum technology
possible.

All 112 inferred edges were reverted, inference is now off by default, and the
score fell back to 93.1. The full exchange is in
`data/INDEPENDENT_AUDIT.md`, including all 37 specific findings and what was
done about each.

The reviewer also found 37 of 70 sampled nodes defective in some way. **Assume
that rate holds**: roughly 600 of 1,176 nodes have at least one defect and
roughly 280 have a serious one. An audit measures an error rate; it does not
repair a tree.

## 3. The value of each choice, measured

Ablation study: remove one node from the strategy so it is never built, and
re-run. On the 1,176-node tree at 60 runs per variant this is **much noisier
than it was on the 128-node tree**, and I am going to report only what survives
the noise rather than dress up a table I do not believe.

**What is unambiguous.** Three nodes take the success rate to **exactly zero**
when removed, and none of them is a technology:

| Node removed | Success | What it is |
|---|---|---|
| `freedman_staff` | **0%** | buying, training and manumitting a technical staff |
| `collegium_licensed` | **0%** | registering the school as a licensed association |
| `citizenship` | **0%** | Roman citizenship, and with it the right of appeal |

Below that, still clearly severe: removing `patron_senatorial` drops it to 5%,
`patron_imperial` to 12%, `semaphore_telegraph` to 20%, `school_founded` to 27%
and `sanitation_antisepsis` to 27%, against a baseline of 87%.

**What I do not trust at this run count.** The "delay in years" column swings
between -12 and +51 and several nodes come out apparently *negative*, which is
noise, not a finding. The 128-node version of this study produced a clean
ordering (corpus 90 years, dispersal 47, press 40, paper 32) and I have left
that result in the record below rather than overwrite it with a worse
measurement, but it was measured on a different and much smaller tree. **Treat
the old ordering as indicative and the new delay figures as not yet measured.**
Running this properly needs a few thousand runs per variant.

The categorical result is what matters and it did not move: **every node whose
removal makes the programme impossible is social or legal, not technical.**

## 3a. The one number that reframes the whole problem

`python3 rome/sim/simulator.py path` reports that the minimum technical closure
of the goal is **158 nodes, 58,850 founder-hours and 9.54 million denarii**
(re-measured against the current 2,833-node tree and the `junction_transistor`
goal; the number of nodes and the money have both grown since the 1,176-node
version this section originally quoted, though the shape of the finding below
has not), against the roughly **72,000 hours** you will ever have.

So on hours alone, one person could in principle direct the entire technical
path to a transistor. It is the other two constraints that make that a fantasy:

1. **The calendar floor is 142 years** and, if mortal, you have about 30. Nitre beds take
   two years whatever you spend. A generation of economic diffusion takes a
   generation. Money buys neither.
2. **Those 158 technical nodes do not include a single one of the nodes that
   provide the money and the people.** No patron, no citizenship, no school, no
   revenue, no printing, no defence against plague. Ablate any of the first
   three and the success rate is zero.

The technical problem is one lifetime of work. The actual problem is three
centuries of institution-building, and that is the problem this project is
really about.


## 3b. Two sweeps that changed how I would play this

`python3 rome/sim/simulator.py sweep capital` and `sweep lifespan`, 200-250 runs
per point. **Read the failure column, not the success column.** When the way you
die changes, the binding constraint has changed and so should your strategy.

### More starting money is not simply better, and on the big tree it is simply worse

`sweep capital`, 60 runs per point, founder immortal.

| Starting capital | Success | Median | Dominant failure |
|---|---|---|---|
| 2,000 den | **72%** | 281 AD | denounced as a magician |
| 5,000 den | 70% | 280 AD | denounced |
| **10,320 den** (the default kit, 3 kg of gold) | 70% | 271 AD | denounced |
| 25,000 den | 67% | 277 AD | denounced |
| 50,000 den | 63% | 280 AD | denounced |
| 200,000 den | 62% | 267 AD | denounced |
| 1,000,000 den | **57%** | 267 AD | denounced |

**This result has changed since the 128-node version and I am reporting the
change rather than the old number.** On the small tree with a mortal founder
there was an optimum around 25,000 to 50,000 denarii: enough money bought speed,
and speed mattered because you were racing your own death. On the big tree with
an immortal founder that counterweight is gone, and **more money is monotonically
worse across the whole range**, from 72% at two thousand denarii down to 57% at a
million.

The mechanism is the same one, now unopposed. Money buys speed, speed produces a
stream of inexplicable marvels, and a stream of inexplicable marvels in Trajanic
Italy gets you prosecuted. Every single row of that table dies the same way.

Practical consequence, and it is a strange one: **arrive poor and stay
inconspicuous.** If you find yourself rich, spend it on public benefaction and on
people, which lower suspicion, rather than on running four projects at once,
which raises it. The optimal amount of gold to carry back is roughly enough for
a house, a workshop and a staff, and no more.

### The founder's lifespan (measured with `--mortal`)

| Years the founder survives | Success | Median | Dominant failure |
|---|---|---|---|
| 10 | **0%** | never | died without successors |
| 15 | **0%** | never | died without successors |
| 20 | 48% | 383 AD | died without successors |
| **28** (the median draw) | **86%** | 379 AD | denounced |
| 35 | 90% | 378 AD | denounced |
| 45 | 88% | 383 AD | denounced |
| 60 | 88% | 372 AD | denounced |

There is a cliff between 15 and 28 years and a plateau after it. Living to 95
buys you almost nothing that living to 63 did not.

**That is the clearest statement of the job.** Your entire task is to get the
school founded and the corpus started before roughly year 20. Everything you
personally build after that is a bonus, and everything you fail to transmit
before then is lost whatever else you achieve. It also means the most valuable
possible use of your medical knowledge is on yourself and your first students,
early: the difference between dying at 15 years in and 28 years in is the
difference between certain failure and 86%.

## 4. The phases

### Phase A - Years 0 to 5. Survive, and start the slow things.
Do nothing impressive for six months. Then, in parallel:
- **nitre beds** (24 months of biology you cannot buy down)
- **lens grinding** (revenue, and the gift that buys your first patron)
- **units and standards** (before you write any recipe down)
- **a patron**, then **citizenship**, then a **licensed collegium**

Cheap wins that cost days and buy goodwill: the horse collar and whippletree,
the crank and connecting rod, the drawplate, hard soap, the world map, the
camera obscura, the single-bead microscope.

### Phase B - Years 5 to 20. Convert money into people.
**Found the school.** This is the pivot of the entire game and every year of
delay costs more than any single technology. Buy skilled slaves, teach them,
free them, pay them, keep them: a manumitted literate artisan transmits
knowledge and a coerced labourer does not, and Roman society is entirely
comfortable with the arrangement.

Start the corpus. 6,000 of your hours over ten years. Do not cut it.

### Phase C - Years 10 to 30. Make knowledge indestructible.
Paper, then oil-based ink, then punchcut type, then the press (Rome already has
the screw press, so you are building half a machine). Then **hundreds of copies
of the corpus, dispersed from Britain to India, in three climates and two
languages.** The lesson of Alexandria is not that books burn. It is that single
copies burn.

### Phase D - Years 15 to 60. The three industrial keys, in order.
1. **Iron.** Water-blown bellows, then the tall shaft furnace and cast iron,
   then the finery and puddling, then cementation and crucible steel. This is
   also the financial engine of the middle game.
2. **Acid.** Green vitriol in a retort, then the lead chamber process. Then
   nitric and hydrochloric from it. Nothing in chemistry happens first.
3. **Precision.** Three plates rubbed in rotation give a true plane from
   nothing. From the plane comes the straightedge, the square, the master
   screw, the lead screw, the micrometer, the bored cylinder, and every
   machine after.

### Phase E - Years 50 to 150. Zinc, then electricity.
**Zinc metal is the hidden gate and almost nobody sees it.** Zinc boils at
907 C, below the temperature at which its ore is reduced, so it leaves as vapour
and reburns, which is exactly why Rome makes brass without ever seeing the
metal. Seal the retort, condense downward. Without zinc there is no voltaic
pile, and without a pile there is no electrochemistry, no electromagnetism, and
no electrical age at all.

Then: pile, Daniell cell, drawn insulated copper wire (silk, oiled linen and
shellac, because you have no rubber and never will), tangent galvanometer,
electromagnet, telegraph, dynamo with self-excitation, transformers, grid.

### Phase F - Years 120 to 280. Vacuum, purity, semiconductors.
Sprengel mercury pump (high vacuum with no machining at all), discharge tubes,
the vacuum tube, then the germanium chain: zinc smelter flue dust, germanium
tetrachloride distilled like brandy at 86 C, hydrogen reduction, zone refining,
Czochralski pulling, and finally two phosphor bronze points a fraction of a
millimetre apart on an n-type slab.

## 5. Three decisions I made deliberately, and why

**Gunpowder is scheduled last, on purpose.** It is cheap, it is easy once the
nitre beds run, and it would buy imperial favour instantly. It would also arm
every provincial usurper for the next two centuries, during exactly the fifty
years when the Empire must not fragment. Develop the nitric acid chemistry,
withhold the corning step, and keep it as a card to play if the programme's
survival requires it.

**Steam is scheduled late.** Italy and Gaul have rivers. Water power gets the
same shaft horsepower for a fraction of the prerequisite tree, and steam is
gated behind cylinder boring anyway. Steam matters when you need power where
there is no river, which is a problem you do not have for a century.

**Public health is a technology node, not a moral aside.** You know the Antonine
Plague arrives in 165 AD. Quarantine, clean water, handwashing and variolation
are nearly free and they are what decides whether your school still exists in
181 AD. It is also, separately, the right thing to do, and the two facts are not
in tension.

## 6. What the model is probably wrong about

Stated plainly, because someone is going to check.

- **The calibration was tuned by me until the output looked defensible, and you
  should discount it accordingly.** The first version of this simulator returned
  a median of 253 AD, which I judged far too fast for a programme that has to
  build a power grid and a railway, so I raised the workforce requirements on the
  heavy nodes and added generational diffusion floors. Those changes were
  reasoned, and they were also chosen because the answer they produced looked
  more plausible to me. That is not an independent measurement. The parts of this
  project that are NOT tuned in that way, and are therefore worth more, are the
  dependency structure, the ablation ORDERING, and the two sweeps in section 3b,
  where the shape of the result (an optimum in starting wealth, a cliff in
  lifespan) was not something I designed for and did not expect.

- **The absolute years.** Trust them to a factor of about 1.5, not better. The
  ordering and the failure modes are far more robust than the dates.
- **The revenue side is the weakest part.** Roman bulk commodity prices marked
  [C] in `data/prices.json` are my estimates anchored to silver through ratios
  implied by the Edict of Diocletian, which is 301 AD and denominated in a
  collapsed currency. The `mirror_amalgam` ablation result above is probably an
  artefact of this weakness.
- **The social model is under-powered.** Denunciation ends only about 2% of
  runs. I believe the true risk to an unprotected foreign chemist in Trajanic
  Italy is materially higher than that, and I could not find a defensible way to
  calibrate it. Treat `03_SOCIAL_POLITICS.md` as better than the number.
- **Slavery is modelled as a labour market with a manumission option.** That is
  a thin treatment of the central economic institution of the society, and it
  understates how much cheap coerced labour suppressed the business case for
  every labour-saving device in this document.
- **There is no competitor, no state seizure of your industry, and no war that
  targets you specifically.** All three are real risks the model ignores.
