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
- Only the orchestrating session may run on a large model. That session should be
  reading, deciding and writing the hard parts, not fanning out Opus workers.

---

## 2. What this project is

A simulator of technological bootstrapping. The current scenario: a
knowledgeable, effectively immortal founder arrives in a historical
civilisation with a technical database and some starting capital; the question
is how fast a modern capability frontier can be reached, and why.

Three artefacts share one dataset:

- `data/` - the tech tree (`python3 sim/simulator.py validate`),
  prices, civilisations, geography.
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

What is allowed as an input: physical constants, material properties,
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

**3.5 There is no save-format migration, ever. Stop designing for one.**
A decision, not an oversight. A game is about half an hour, nobody is forced
to update, and anyone running one stays on the version they started on. A save
written by an old build does not have to load in a new one.

So: rename a persisted field, drop one, change its units, restructure the
whole save. No shim, no version stamp, no upgrade path, no `if "old_key" in
data`. Every agent that has looked at this has independently invented a
migration plan for a problem this project does not have; do not be the next
one.

What this does NOT excuse: save/load still has to work within a build. The
suite exercises it hard, and with `--session` every single command is a save
followed by a load, so a field that fails to round-trip breaks the game in
normal play. `SAVE_FIELDS` still matters. Its history does not.

**3.6 DO not save hard numbers to any md file or comments.**
The file changes a lot, and the hard numbers have constantly had to be replace.

**3.7 Keep comments short and concise about the current code.**
Comments keep refrencing the past code, previous changes, quoting people, etc. Comments should describe what the code does now, not why it was changed or what code came before it. Comments should also use inline comments more, right now most comments are header style, which means a lot of comments are 10+ lines long. The code base is currenly massively commented focused, making it about 2x as big as it needs to be.

---

## 4. Architecture direction

`docs/architecture/` holds this project's design documents; read its README
first, since it says which apply and in what order. The live
plan is `ENDOGENOUS_COSTS_AND_DOMAINS.md`: how a price gets calculated rather
than looked up, which domains produce prices and which only consume them, and
the milestones. `PM_ASSESSMENT.md` is the reasoning behind it. The two
external design documents are saved verbatim as inputs to both, and are
direction rather than approved plans.

Two things from the plan worth knowing before you touch anything:

**`data/production/` is the production side.** The tree
records what every process consumes and nothing about what anything produces,
which is why every cost bottomed out in a book value: there was no physical structure to compute one from.
`prices.json` is the old way, and needs to be deleted asap.

`data/production/` covers **most of the consumption sites** `python3 sim/validate_production.py` for current coverage).
Read `data/production/_SCHEMA.md` before adding to it. The rule
that governs every number there: a yield is a physical fact - ore grade times
recovery, reaction stoichiometry, latent heat - and is NEVER derived from what
the material sells for, nor tuned so a computed price matches `prices.json`.
Those prices are mostly estimates and this data exists to
replace them.

    python3 sim/validate_production.py          errors and coverage
    python3 sim/validate_production.py --todo   what is still missing
    python3 sim/audit_costs.py                  where the cost base is

**Nothing reads this data yet.** The price solver described in
`ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 2 is the next piece, and until it
exists the engine still uses `prices.json`. Coverage is not the same as
being wired in. This needs to be changed.

Make the founder's mechanisms general enough that other actors can use
them, rather than making the founder less detailed.
This needs to be changed, as the game is becoming multiplayer.
Eventually, we want to treat even th other countries as their own players.

---

## 5. Commands you will need

```bash
python3 sim/simulator.py validate          # after EVERY edit to data/
python3 sim/test_regressions.py            # full suite (~68s)
python3 sim/test_regressions.py --list     # topic names
python3 sim/test_regressions.py --only mines,demographics
python3 sim/perf_fingerprint.py record before.json   # proves behaviour unchanged
python3 sim/perf_fingerprint.py check before.json
python3 sim/treetool.py judge             # judge nodes (reports; --write to commit)
python3 sim/audit_costs.py                 # how much of the cost base is calculated
python3 sim/audit_costs.py --materials     # every material, and whether anything makes it
python3 sim/repro_nondeterminism.py        # the determinism bug; now passes, kept as a probe
python3 sim/prove_rename_safe.py HEAD      # prove a rename changed nothing but names
```

The suite runs from a checkout of any name, in any directory. If you find
anything that depends on the checkout being called `rome`, it is a bug; see
`sim/tests/test_suite_portability.py`.

---

## 6. Traps that have already bitten someone

- **Green tests do not mean unchanged behaviour.** The suite asserts on
  outputs and messages, not on the simulation being the same simulation.
  `perf_fingerprint.py` covers that, and it works again as of this branch -
  a record and a check against the same checkout come back byte-identical on
  all nine scenarios. It still does not cover `protocol.py`, where a third of
  the code lives.
- **The tree tools write to the repository only when asked.**
  `treetool.py merge|judge|repair|apply-caps` each rewrite a committed data
  file, and each reports by default and writes nothing. `--write` is what
  commits the result.

- **`Sim` is one god object.** Every mixin method talks through `self`, so
  the coupling is real however the files are arranged. A full decomposition
  has been considered and currently trying to be changed, in `sim/ARCHITECTURE.md`.

- **Much of the engine is majority comment, and the comments are excessive.**
  They are how agents hand each other the reason a thing is the way it is. If you come across a comment that is more than 10 lines long, it is likely excessive. If the comment doesn't help, and is just excessive, delete it.

- **`_internal` fields are for auditors, `note` fields are for players.**
  Never put an audit marker where a player will read it.

---

## 7. Naming

Identifiers two characters or shorter: `python3 sim/code_health.py --names`

**Three commands.** `code_health.py --names` gives
the burndown total. `.pylintrc` turns pylint into the worklist - every short
name it can see comes back as a `file:line` somebody can fix:

    python3 -m pylint sim/ | grep -c C0103

Pylint's `invalid-name` check is driven by
how pylint CLASSIFIES a binding, and three classifications carry no name
check at all: a module-level name bound to a CALL (`KB = os.path.join(...)`
is invisible while `QQ = 5` one line below is reported), a module-level loop
target, and a lambda parameter. Measured: `python3 sim/pylint_blind_spots.py`

This codebase keeps most of its short names exactly where pylint is quietest -
the test suite is written as module-level script code rather than as
functions. Use pylint for the worklist and that script for what the worklist
cannot see.

**The rule for new and edited code:** spell names out. The only acceptable
short names are `i` as a loop index, and `x`/`y` as coordinates, and only
inside a scope short enough to see whole. Everything else gets a word:
`node`, `node_id`, `sim`, `trade`, `material`, `rate`, `key`, `total`.

**This applies to prose, docstrings and design documents, and it is the rule
most often broken.** `p = A'p + w.l + rents` is four letters standing for
four things nobody can recover without the textbook. So is

    q_i = gamma_i + (beta_i / p_i) * (Y - sum_j p_j * gamma_j)

A reader with no economics has no way to tell that from a radiation equation.
Write it out:

    quantity_of_good = subsistence_floor_of_good + marginal_budget_share_of_good / price_of_good * (income - cost_of_all_subsistence_floors)

**Fix bad names you pass through, where it is cheap.** If you are editing a
function and it has a one-letter local whose meaning you have just had to
work out, rename it while you are there - you have already paid the
expensive part, which is understanding it.

A sweep is planned; see `docs/architecture/NAMING_PLAN.md` for the tiering,
the per-name meanings and the tooling. `python3 sim/code_health.py --names`
prints today's Tier-1 share; quote that, not NAMING_PLAN.md's, for current
state. Tier 1 is a purely local variable, provably safe to rename; a
function PARAMETER is Tier 2, because `prove_rename_safe.py` cannot cover a
caller passing by keyword.

`python3 sim/prove_rename_safe.py <ref>` proves a rename changed nothing but
names, by comparing compiled bytecode: a local's name is not in `co_code`, so
a pure local rename leaves the executed bytes identical, while an attribute or
global moves `co_names` and a literal moves `co_consts`. That is a proof over
every possible run rather than a sample of nine, and it does not depend on
`perf_fingerprint` working.

---

## 8. Working habits this repo expects

- Every discovered bug becomes a regression test with the smallest scenario
  that reproduces it. See `Complaints/` and `sim/tests/`.
- Every number asserted in a prose document must have been computed by the
  simulator. Prose quotes the data; it never asserts it.
- Claims about the codebase should be measured, not remembered. If you change
  the shape of the code, re-measure the counts in `sim/ARCHITECTURE.md`.
- **Standing rule, added after the stakeholder flagged documentation going
  stale silently: a number in prose should instead carry the idea, and the command or script that
  produced it, remove the number, it should not go in.** This file
  has already shipped wrong node counts and wrong file counts that nobody
  caught because nothing next to the number said how to check it. Where a
  command genuinely does not exist yet (a throwaway scan that was never
  committed, for instance), say so explicitly in the same sentence instead
  of leaving the number to look authoritative. A number with neither a
  command nor an "unverifiable" label next to it is a bug in this file.

    Do TDD where possible. If asked to fix a bug, add a feature, or refactor something:
    add a regression test first, then make the test pass. If you can't see what it is currently doing in a test, then you can't fix it.
    Ask for more information to understand the current behavior to actually add a test. Otherwise, if you try to fix it with your best guess, you will likely make it worse.

    Make things abstracted and dynamic where we can. An example that we had to redo is the save file. It was previously hard coded every variable that needed to be saved, and had to be constantly updated. Instead, it now detects fields automatically, and only excludes fields that are not needed. This allows for much easier expansion of the game without having to update the save file format. Same should apply to most of the game. If you have to manually update a bunch of files every time you add a new feature, you are doing it wrong.
