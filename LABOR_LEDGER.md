# LABOUR LEDGER

Two ledgers, because two different people did work on this project.

---

# PART 1 - The founder's personal hours (in the game)

Your own hours are the binding constraint of the whole enterprise. Money is
recoverable; a year of your attention is not. This ledger is computed from 300
simulated lifetimes under the recommended strategy.

**Budget:** about 2,400 useful hours a year. Roman elite males who reached 35
could expect roughly another 25 to 30 years, so call it 30 years and 72,000
hours, total, forever.

| | |
|---|---|
| Median years the founder survives after arrival | **29** |
| 10th / 90th percentile | 18 / 39 years |
| Median founder-hours actually delivered in a lifetime | **39,132** |
| Founder-hours the full tree demands | 215,600 |
| Those hours as a share of the tree's total founder-hour demand | **18%** |

### What the founder personally lives to see finished

Share of 300 runs in which this node was complete before the founder died.

| Node | Completed before death | Tier |
|---|---:|---:|
| `workshop_first` | 100% | 1 |
| `patron_local` | 100% | 0 |
| `world_map` | 100% | 0 |
| `arithmetic_positional` | 100% | 0 |
| `units_standards` | 100% | 0 |
| `identity_cover` | 100% | 0 |
| `horse_collar` | 100% | 1 |
| `arrival_orientation` | 100% | 0 |
| `citizenship` | 100% | 0 |
| `scientific_method` | 99% | 0 |
| `nitre_beds` | 99% | 2 |
| `lens_grinding` | 97% | 1 |
| `glass_bead_microscope` | 97% | 1 |
| `case_hardening` | 97% | 1 |
| `soap_hard` | 97% | 1 |
| `drawplate_wire` | 97% | 1 |
| `crank_conrod` | 96% | 1 |
| `potash_soda` | 96% | 1 |
| `refractory_fireclay` | 95% | 2 |
| `camera_obscura` | 95% | 1 |
| `glass_clear` | 92% | 1 |
| `freedman_staff` | 92% | 1 |
| `collegium_licensed` | 88% | 1 |
| `glass_labware` | 88% | 2 |
| `water_power_scale` | 87% | 1 |
| `mirror_amalgam` | 84% | 1 |
| `distillation_alcohol` | 83% | 1 |
| `lead_metallurgy` | 71% | 1 |
| `school_founded` | 71% | 1 |
| `algebra_symbolic` | 69% | 0 |
| `crude_cell` | 67% | 1 |
| `charcoal_industrial` | 57% | 2 |
| `corpus_written` | 54% | 1 |
| `germ_theory` | 53% | 0 |

Nodes reached in fewer than half of runs before the founder dies, and therefore
things you should assume you will NOT live to see:

`cementation_steel`, `precision_three_plate`, `telescope`, `bellows_water_blown`, `blast_furnace`, `statistics_basic`, `geometry_analytic`, `lab_apparatus`, `sulfuric_retort`, `mercury_supply`, `nitric_acid`, `hydrochloric_acid`, `barometer`, `thermometer`, `master_screw`, `balance_analytical`, `atomic_theory`, `calculus`, `finery_puddling`, `coal_coke`, `crucible_steel`, `copper_fire_refined`, `zinc_metal`, `newtonian_mechanics`, `em_theory`, `screw_lathe`, `micrometer_gauges`, `lead_chamber`, `voltaic_pile`, `copper_refining` ...

## The single most important number in this project

**18%.** Your entire working life delivers under a fifth of the founder-hours
the tree demands. And that is the flattering way to put it, because those hours are
spread across retries and abandoned attempts, not neatly banked against finished
nodes. You are not the builder of a transistor. You are the first link in a
relay of many generations of directors, and the only things you
can hand forward are trained people and written words.

Which is why the corpus is 6,000 hours, about 17% of everything you will ever
deliver, and why the ablation study says cutting it costs 90 years.

## The allocation rule, restated as arithmetic

For any task, ask: **can a hired Roman do it if I specify it?**

| | Founder-hours | Hired-hours | Do it yourself? |
|---|---|---|---|
| Grinding a lens | 1 | 1 | No. Specify it once, hire it forever. |
| Running a furnace campaign | 1 | 1 | No. |
| Teaching a student calculus | 1 | 0 | **Yes. Nobody else can.** |
| Writing the corpus | 1 | 0.5 (a scribe copies) | **Yes.** |
| Deciding what to build next | 1 | 0 | **Yes.** |
| Debugging a process that has never worked | 1 | 0.3 | Yes, at first, then hand it over. |

Every simulated run that fails is a founder who got this wrong.

---

# PART 2 - The author's hours (building this guide)

Recorded because the exercise asked for it and because a tool should say how it
was made.

## Division of labour

**Round 1: the 128-node version**

| Work | Done by |
|---|---|
| Branch setup, repository structure, world state, social model, non-obvious tricks index, the 128-node core spine, prices, the simulator, the strategies, all prose | author |
| 11 knowledge modules (10 through 99) | 10 Sonnet subagents, 5 at a time |
| Adversarial fact-check of modules 10, 20, 30, 40 | 1 Sonnet subagent |

**Round 2: the rebuild to 1,176 nodes**

| Work | Done by |
|---|---|
| Capability rung layer (33 nodes) and material layer (77 nodes) | author. These are the load-bearing correction and were not delegated. |
| The CONTRACT and VOCABULARY the branch authors worked to | author |
| 15 domain branches, 1,048 nodes | 15 Haiku subagents in parallel |
| `treetool.py` (merge, repair, apply-caps, judge) | author |
| Simulator changes: immortality default, reputation, bug fixes | author |
| 5 new knowledge modules (90 through 94) | 5 Haiku subagents |
| **Independent audit of 70 sampled nodes** | 1 Sonnet subagent, deliberately given no sight of the author's own checker |
| Node-by-node capability assignment, 318 nodes | 5 Haiku subagents |

Agent budget observed throughout: never more than 5 Sonnet-equivalents at once,
counting 3 Haiku as 1 Sonnet.

## Why the split fell that way

The subagents got the *breadth* work: ten deep technical modules, each 4,000 to
10,000 words, which is simply a lot of typing. The author kept everything where
a single wrong number propagates: the tech tree, the price model, the simulator,
and the strategy conclusions drawn from them. A hallucinated detail inside a
metallurgy recipe is a bug in one paragraph. A wrong prerequisite edge in
`tech_tree.json` silently corrupts every result the simulator produces.

That is the same allocation rule as Part 1, applied to this document: delegate
what can be specified, keep what cannot.

## The most important thing that happened in round 2

I wrote a repair script that inferred missing capability prerequisites by
matching keywords against each node's prose. It added 112 edges and my own audit
score rose from 80.8 to 98.0.

The independent reviewer then sampled 70 nodes and found that **every one of the
eight carrying an inferred prerequisite was wrong.** A 1300 C blast furnace rung
on a room-temperature explosives mix. A 1600 C furnace on a paperwork node about
binary arithmetic. A vacuum rung on mercury extraction, which reverses the
dependency, because mercury is what makes vacuum technology possible.

All 112 were reverted. Inference is off by default. The score fell to 93.1.

**I had already written, in round 1, that the danger was "my own checker being
satisfied by my own repair", and then I did exactly that anyway.** Noticing a
failure mode in prose is not the same as avoiding it. The thing that caught it
was an outside reviewer with no sight of my heuristics, which is the only reason
this project has a trustworthy number anywhere in it.

## Verification actually performed

- `simulator.py validate` on every edit: DAG acyclicity, no dangling
  prerequisites, every material priced, every trade waged.
- Deliberate traps planted in the agent brief (Roman *nitrum* is not saltpetre;
  no cast iron in the Roman West; no rubber; no New World crops) and then
  grepped for in the returned files. All four held. One agent independently
  caught and corrected two anachronisms it had introduced itself, in a draft the
  author had not seen.
- Every headline number in `02_STRATEGY.md` and `04_ECONOMICS.md` recomputed
  from the data files rather than quoted from memory.

## Known unverified

- The Larderello boric acid claim is geologically sound and its Roman-era
  exploitation is unattested. Marked [C] and flagged in three places.
- Bulk metal prices are anchored to a 301 AD document. Marked [C] throughout.
- The subagent modules were checked for the planted traps and for internal
  format compliance. They were **not** line-by-line fact-checked. Treat any
  single number inside a knowledge module as [C] unless it carries its own
  MEASURED tag.
