# CLAUDE.md - working agreement for AI agents on this repo

This is a simulation project built by AI agents, for AI agents. Read this file
before touching anything. It is short on purpose; the long documents it points
at are the real reference.

---

## 1. Subagent policy (hard rule)

When spawning subagents with the `Agent` tool:

- **Allowed:** Sonnet and Haiku.
- **Forbidden:** Opus and Fable. They burn too much usage budget. Do not spawn
  them, do not "just this once" them, do not route around this by asking
  another agent to spawn one.
- **Budgeting:** one Sonnet agent costs about the same as three Haiku agents.
  If a job splits cleanly into three independent Haiku-sized pieces, prefer
  three Haiku over one Sonnet - same cost, more parallelism.
- **Choosing:** Haiku for mechanical work with a clear spec (grep sweeps, file
  inventories, applying a stated edit pattern, running a test topic and
  reporting failures). Sonnet for work that needs judgement (reading code to
  explain why something behaves as it does, designing a small mechanism,
  reviewing a diff for realism defects).
- Only the orchestrating session runs on a large model. That session should be
  reading, deciding and writing the hard parts, not fanning out Opus workers.

---

## 2. What this project is

A simulator of technological bootstrapping. The current scenario: a
knowledgeable, effectively immortal founder arrives in a historical
civilisation with a technical database and some starting capital; the question
is how fast a modern capability frontier can be reached, and why.

Three artefacts share one dataset:

- `data/` - the tech tree (2,849 nodes), prices, civilisations, geography.
- `knowledge/` - how to physically do each thing the tree names.
- `sim/` - the engine, the CLI/JSON protocol, and the test suite.

Read `README.md` for the layout and `sim/ARCHITECTURE.md` for how the engine is
actually shaped (it is measured, not remembered - keep it that way).

---

## 3. The design constraints that govern every change

These come from the project's requirements, not from taste. When a change
conflicts with one of these, the change is wrong.

**3.1 No hardcoded outcomes.** Do not encode a historical result that the
simulation should be able to produce from lower-level state. A Roman soldier
must not cost 100 denarii because history says so; his cost must fall out of
food, labour scarcity, equipment, transport, recruitment institutions and risk.
The same applies to city sizes, army sizes, state revenue, wages, adoption
timing and industrial output.

What *is* allowed as an input: physical constants, material properties,
biological limits, geography, and initial conditions (the population in 100 AD,
which mines are open, what is already known). See
`docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md` §2.2 and §10.

**3.2 The historical record must be a plausible outcome, not the only one.**
Settled with the stakeholder. With no intervention, the real trajectory should
be a plausible draw from an ensemble of baseline runs - validated against
distributions and relationships (population ranges, urbanisation share,
wage-to-grain ratios, technology appearance windows), never against dated
events. If the baseline reliably reproduces the Antonine plague in 165 AD,
that is evidence we cheated, not evidence it works.

The baseline is explicitly allowed to get worse while the mechanisms that will
make it good are being built. Every step toward endogeneity costs historical
match in the short run, and there is no path that avoids it.

**3.3 Interventions propagate through normal rules.** A gold deposit is a
resource stock at a location. Rifles are objects with ammunition and
maintenance requirements. Dragons are agents with calorie needs. None of them
get a bespoke outcome branch.

**3.4 Label every heuristic you cannot yet derive.** Transitional shortcuts are
allowed while the deeper mechanism does not exist. Unlabelled ones are not.
Tag them so the migration queue is measurable.

---

## 4. Architecture direction

`docs/architecture/` holds four documents; read its README first. The live
plan is `ENDOGENOUS_COSTS_AND_DOMAINS.md`: how a price gets calculated rather
than looked up, which domains produce prices and which only consume them, and
the milestones. `PM_ASSESSMENT.md` is the reasoning behind it. The two
external design documents are saved verbatim as inputs to both, and are
direction rather than approved plans.

Two things from the plan worth knowing before you touch anything:

**The tree has no production side.** It records what every process consumes
and almost never what anything produces. Of 162 materials consumed, zero have
a producing node that declares a yield; `iron_bar_kg` is consumed by 590 nodes
and nothing makes it. That, and not the existence of `prices.json`, is why
every cost bottoms out in a book value. Run `python3 sim/audit_costs.py`.

**Make the founder's mechanisms general enough that other actors can use
them**, rather than making the founder less detailed.

---

## 5. Commands you will need

```bash
python3 sim/simulator.py validate          # after EVERY edit to data/
python3 sim/test_regressions.py            # full suite (~68s)
python3 sim/test_regressions.py --list     # topic names
python3 sim/test_regressions.py --only mines,demographics
python3 sim/perf_fingerprint.py record before.json   # SEE THE WARNING IN 6
python3 sim/perf_fingerprint.py check before.json
python3 sim/treetool.py judge --dry-run    # judge nodes in isolation
python3 sim/audit_costs.py                 # how much of the cost base is calculated
python3 sim/audit_costs.py --materials     # every material, and whether anything makes it
python3 sim/repro_nondeterminism.py        # the determinism bug, in ten seconds
```

The suite runs from a checkout of any name, in any directory. If you find
anything that depends on the checkout being called `rome`, it is a bug; see
`sim/tests/test_suite_portability.py`.

---

## 6. Traps that have already bitten someone

- **Green tests do not mean unchanged behaviour.** The suite asserts on
  outputs and messages, not on the simulation being the same simulation.
  `perf_fingerprint.py` is supposed to cover that, and it does not cover
  `protocol.py`, where a third of the code lives.
- **The simulation is not deterministic, and `perf_fingerprint.py` therefore
  proves nothing.** The same scenario, same seed, run four times in one
  process, gives more than one answer; the difference is 1.3e-12 in a float
  and it compounds over two centuries. Reproduce it in ten seconds with
  `python3 sim/repro_nondeterminism.py`. Until it is fixed, **a clean
  `check` proves nothing and a dirty one accuses nothing** - do not start a
  refactor of the simulation loop behind it. Everything ruled out so far is
  in `Complaints/27-nondeterministic-simulation.md`; read it before
  investigating, several obvious hypotheses are already dead.
- **The tree tools write to the repository.** `treetool.py merge|judge|repair|
  apply-caps` each rewrite a committed data file. Pass `--dry-run` if you only
  meant to look.
- **`Sim` is one god object** - ~157 attributes, ~314 methods, six mixins that
  all talk through `self`. A full decomposition has been considered and
  rejected with reasons in `sim/ARCHITECTURE.md`. Do not silently restart it.
- **Five of eight engine files are majority comment.** The comments are how
  agents hand each other the reason a thing is the way it is. They are
  load-bearing. Do not strip them to "clean up".
- **`_internal` fields are for auditors, `note` fields are for players.**
  Never put an audit marker where a player will read it.

---

## 7. Naming

An AST scan counts **3,813 bindings of identifiers two characters or shorter,
across 332 distinct names and 83 files**: `k` alone is 568 bindings in 53
files, `s` is 264, `n` is 198, `r` is 197. That is the single biggest
obstacle to anyone reading this code, and it gets worse every time someone
adds to it.

**The rule for new and edited code:** spell names out. The only acceptable
short names are `i` as a loop index, and `x`/`y` as coordinates, and only
inside a scope short enough to see whole. Everything else gets a word:
`node`, `node_id`, `sim`, `trade`, `material`, `rate`, `key`, `total`.

This applies to prose and design documents too. `p = A'p + w·l + rents` is
four letters standing for four things nobody can recover without the
textbook - write `price_of(good)`, `hours_per_unit`, `wage_of(trade)`.

A sweep of the existing 3,813 is planned; see
`docs/architecture/NAMING_PLAN.md` for the tiering and the tooling. Purely
local variables are safe to rename mechanically. The tech-tree DATA schema
fields (`lab`, `mat`, `cap`, `rev`, `up`, `ph`, `sch`, `art`, `sus`, `gov`,
`conf`, `pre`, `yrs`, `kb`) are a separate and much harder problem: they are
in 2,864 nodes of JSON, in save files, and in the protocol, so changing them
is a data migration with a compatibility shim, not a refactor. Do not start
it casually.

---

## 8. Working habits this repo expects

- Every discovered bug becomes a regression test with the smallest scenario
  that reproduces it. See `Complaints/` and `sim/tests/`.
- Every number asserted in a prose document must have been computed by the
  simulator. Prose quotes the data; it never asserts it.
- Claims about the codebase should be measured, not remembered. If you change
  the shape of the code, re-measure the counts in `sim/ARCHITECTURE.md`.
