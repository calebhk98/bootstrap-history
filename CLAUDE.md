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

**3.2 The baseline must still look like our timeline.** With no intervention,
an ensemble of runs should sit inside the historically plausible region -
without getting there by scripting the answer. This constraint and 3.1 pull
against each other; that tension is the central engineering problem of the
project, not a detail.

**3.3 Interventions propagate through normal rules.** A gold deposit is a
resource stock at a location. Rifles are objects with ammunition and
maintenance requirements. Dragons are agents with calorie needs. None of them
get a bespoke outcome branch.

**3.4 Label every heuristic you cannot yet derive.** Transitional shortcuts are
allowed while the deeper mechanism does not exist. Unlabelled ones are not.
Tag them so the migration queue is measurable.

---

## 4. Architecture direction

Two reference documents live in `docs/architecture/`:

- `HISTORICAL_SIM_ARCHITECTURE.md` - the target model: shared world state,
  stocks/flows/processes/constraints, capability frontiers, actor-owned
  knowledge, endogenous prices.
- `CURRENT_CODE_ARCHITECTURE_REVIEW.md` - a review of this repo against that
  target, recommending in-place expansion rather than a rewrite.

Treat both as direction, not as an approved plan. Where they disagree with a
decision recorded in this repo, the repo's recorded decision wins until it is
explicitly revisited.

The agreed direction in one line: **make the founder's mechanisms general
enough that other actors can use them**, rather than making the founder less
detailed.

---

## 5. Commands you will need

```bash
python3 sim/simulator.py validate          # after EVERY edit to data/
python3 sim/test_regressions.py            # full suite (~68s)
python3 sim/test_regressions.py --list     # topic names
python3 sim/test_regressions.py --only mines,demographics
python3 sim/perf_fingerprint.py record before.json
python3 sim/perf_fingerprint.py check before.json   # proves behaviour unchanged
python3 sim/treetool.py judge --dry-run    # judge nodes in isolation
```

---

## 6. Traps that have already bitten someone

- **Green tests do not mean unchanged behaviour.** The suite asserts on
  outputs and messages, not on the simulation being the same simulation. Use
  `perf_fingerprint.py` for that. It does not cover `protocol.py`.
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

## 7. Working habits this repo expects

- Every discovered bug becomes a regression test with the smallest scenario
  that reproduces it. See `Complaints/` and `sim/tests/`.
- Every number asserted in a prose document must have been computed by the
  simulator. Prose quotes the data; it never asserts it.
- Claims about the codebase should be measured, not remembered. If you change
  the shape of the code, re-measure the counts in `sim/ARCHITECTURE.md`.
