# CLAUDE.md - working agreement for AI agents on this repo

This file holds what changes slowly: what the project is, the rules, the
coding patterns, and where to look. Anything that changes from week to week
(status, coverage, counts, which module is wired to which, exact file paths
inside a package) belongs in the documents it points at, not here. If you are
about to add a sentence that will be false after the next few merges, put it
in a status document instead.

---

## 1. Subagent policy (hard rule)

When spawning subagents with the `Agent` tool:

- **Allowed:** Sonnet and Haiku.
- **Forbidden:** Opus and Fable. They burn too much usage budget. Do not spawn
  them, do not "just this once" them, do not route around this by asking
  another agent to spawn one.
- **Budgeting:** one Sonnet agent costs about the same as three Haiku agents.
  A normal batch is roughly five Sonnet-equivalents running at once, mixed
  however suits the work.
- **Choosing:** Haiku for mechanical work with a clear spec (grep sweeps, file
  inventories, applying a stated edit pattern, running a test topic and
  reporting failures). Sonnet for work that needs judgement (reading code to
  explain behaviour, designing a small mechanism, reviewing a diff).
- **Name the branch for what it does** before starting work (for example
  `mods-removal-and-civ-patching`), renaming an auto-generated name if the
  session gave you one. Renaming a branch needs no history rewrite.
- **Parallel agents that edit code** run in separate worktrees and should be
  given tasks that touch different files. Say in each prompt which files the
  other agents own.
- Only the orchestrating session may run on a large model. It reads, decides,
  writes the hard parts and merges.

---

## 2. What this project is

A simulator of technological bootstrapping. The scenario: a knowledgeable,
effectively immortal founder arrives in a historical civilisation with a
technical database and some starting capital; the question is how fast a
modern capability frontier can be reached, and why. The game is becoming
multiplayer, and eventually other countries will be players too, so every
mechanism the founder uses must be usable by any actor.

Three artefacts share one dataset:

- **Data** (`data/`): the tech tree (authored per domain in `data/branches/`,
  built at load by `sim/engine/tree_source.py`), production recipes
  (`data/production/`),
  civilisations, world geography, trades.
- **Knowledge** (under `docs/`): how to physically do each thing the tree
  names. Tree nodes link to it through their `kb` field (`file.md#anchor`).
- **Simulator** (`sim/`): the engine, the CLI/JSON protocol, tools, tests.

---

## 3. Where things live

Check with `ls` before trusting this; directories move.

| Looking for | Look in |
|---|---|
| Engine (the `Sim` object and its mixins) | `sim/engine/` |
| Standalone domain models (agriculture, demography, land, deposits, transport, demand, labour market, ...) | `sim/world/` |
| Actors other than the world (households, later firms/states/players) | `sim/engine/actors/` |
| Price solver | `sim/solve_prices*.py`, `sim/engine/prices.py` |
| CLI and agent/JSON protocol | `sim/simulator.py`, `sim/engine/cli*.py`, `sim/engine/proto/`, `sim/PROTOCOL.md` |
| Tests | `sim/tests/`, run through `sim/test_regressions.py` |
| Engine shape, measured | `sim/ARCHITECTURE.md` |
| Design direction, plans, current status | `docs/architecture/` - read its `README.md` first; it names the live plan and the status document |
| Open problems, bug reports (each has a `**Status:**` line) | `Complaints/` (open), `Complaints/closed/` (done); `python3 sim/issue_status.py` prints the table, `--check` validates it |
| Playtest and audit reports; standing design decisions | `Complaints/reports/`; `docs/architecture/DESIGN_PRINCIPLES.md` |
| Mods: loader, contract, backlog | `sim/engine/mods.py`, `mods/README.md`, `mods/TASKS.md` |
| Playtest setup for agent players | `playtest/` |
| Schema for production data | `data/production/_SCHEMA.md` |

**What to work on next:** the status document in `docs/architecture/`
(its README says which) keeps the ordered to-do list; `Complaints/` holds the
issue backlog. Re-measure a claim there before acting on it, since status
documents lag the code.

---

## 4. Design constraints that govern every change

These come from the project's requirements, not from taste. When a change
conflicts with one of these, the change is wrong.

**4.1 No hardcoded outcomes.** Do not encode a historical result that the
simulation should produce from lower-level state. A Roman soldier must not
cost 100 denarii because history says so; his cost must fall out of food,
labour scarcity, equipment, transport, recruitment institutions and risk.
Same for city sizes, army sizes, state revenue, wages, adoption timing and
industrial output. Allowed inputs: physical constants, material properties,
biological limits, geography, and initial conditions (population at the start
date, which mines are open, what is already known).

**4.2 The historical record is a plausible outcome, not the only one.** With
no intervention, the real trajectory should be a plausible draw from an
ensemble of baseline runs, validated against distributions and relationships
(population ranges, urbanisation share, wage-to-grain ratios, technology
windows), never against dated events. A baseline that reliably reproduces a
specific dated plague is evidence of cheating. The baseline may get worse
while the mechanisms that will make it good are built.

**4.3 Interventions propagate through normal rules.** A gold deposit is a
resource stock at a location. Rifles are objects with ammunition and
maintenance. Dragons are agents with calorie needs. None get a bespoke branch.

**4.4 Label every heuristic you cannot yet derive.** Transitional shortcuts
are allowed while the deeper mechanism does not exist; unlabelled ones are
not. Tag them so the migration queue is measurable.

**4.5 Prices are calculated, not looked up.** There is no price table (the
old `data/prices.json` is deleted); do not add one back. A production yield is
a physical fact (ore grade times recovery, stoichiometry, latent heat), never
derived from a sale price or tuned so a computed price matches the book.

**4.6 No save-format migration, ever.** A game is about half an hour and
players stay on the build they started with. Rename, drop or restructure
persisted fields freely: no shim, no version stamp, no `if "old_key" in
data`. Save/load must still round-trip within a build (with `--session`,
every command is a save then a load).

**4.7 The engine never special-cases content ids.** No `if civ == "rome"`,
no `if node == "steam_engine"`. Content is data so that mods and new
scenarios work without engine edits.

---

## 5. Coding patterns

- **Short files.** Many agents edit this repo at once, and a large file is a
  merge conflict waiting to happen. Split a growing module by topic using the
  existing pattern (`labour.py`, `labour_wages.py`, `labour_training.py`, ...).
  Prefer a new small module over growing a large one.
- **Dynamic over enumerated.** If adding a feature means updating a list in
  several places, the design is wrong. The save file is the model: fields are
  detected automatically and only exclusions are listed.
- **General actors.** Write mechanisms against an actor, not against the
  founder, so a firm, a state or another player can use them.
- **`Sim` is a god object.** Mixin methods talk through `self`, so coupling
  is real however the files are split. Decomposition direction is in
  `sim/ARCHITECTURE.md` and `docs/architecture/`.
- **Comments** describe what the code does now, briefly, preferably inline.
  No history, no "previously", no quotes from people, no multi-paragraph
  headers. A comment longer than about ten lines is probably excessive;
  delete what does not help.
- **No hard numbers in comments or markdown.** Numbers go stale. Give the
  idea and the command that measures it. Where no command exists, say so in
  the same sentence.
- **`_internal` fields are for auditors, `note` fields are for players.**
  Never put an audit marker where a player will read it.
- **Portability.** The suite must run from a checkout of any name in any
  directory.

### Naming

Spell names out. The only acceptable short names are `i` as a loop index and
`x`/`y` as coordinates, in a scope short enough to see whole. Everything else
gets a word: `node`, `node_id`, `material`, `rate`, `total`. This applies to
prose, docstrings and formulas in design documents too:

    quantity_of_good = subsistence_floor_of_good + marginal_budget_share_of_good / price_of_good * (income - cost_of_all_subsistence_floors)

not `q_i = gamma_i + (beta_i / p_i) * (Y - sum_j p_j * gamma_j)`.

Rename a bad local you pass through once you have worked out what it means.
Tooling: `python3 sim/code_health.py --names` (burndown),
`python3 -m pylint sim/ | grep C0103` (worklist), `python3 sim/pylint_blind_spots.py`
(what pylint cannot see), `python3 sim/prove_rename_safe.py <ref>` (proves a
rename changed only names, via bytecode). Plan: `docs/architecture/NAMING_PLAN.md`.

---

## 6. Working habits

- **TDD.** For a bug, feature or refactor: write a regression test that shows
  the current behaviour first, then change the code. If you cannot see what it
  does in a test, you cannot fix it; ask for more information rather than
  guessing.
- **Every bug becomes a regression test** with the smallest reproducing
  scenario. Resolved complaints move to `Complaints/closed/`.
- **Measure, don't remember.** Claims about the codebase are measured. Every
  number in prose was computed by the simulator, and carries the command that
  produced it.
- **Slow checks run before a pull request.** The default run skips them to
  stay fast for local work; run `--slow` before opening a PR (and now and then
  on a long branch), and fix what it finds there.
- **Green tests do not mean unchanged behaviour.** The suite asserts on
  outputs and messages. `sim/perf_fingerprint.py` checks the simulation
  itself (it does not cover the protocol layer).
- **The tree is built, not committed.** `data/tech_tree.json` is generated from
  `data/branches/` at load and is not in git. `treetool.py` reports; only
  `judge --write` writes to data files.

---

## 7. Commands

Most scripts take `--help`. The ones used most:

```bash
python3 sim/simulator.py validate          # after EVERY edit to data/
python3 sim/validate_production.py         # production data errors and coverage (--todo for gaps)
python3 sim/test_regressions.py            # full suite, parallel across available cores (--jobs 1 sequential, --list, --only a,b, --slow)
python3 sim/perf_fingerprint.py record before.json   # then `check before.json` to prove behaviour unchanged
python3 sim/audit_costs.py                 # how much of the cost base is calculated
python3 sim/treetool.py judge              # judge tree nodes (--write to commit)
```
