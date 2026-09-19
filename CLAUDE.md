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

- `data/` - the tech tree (2,864 nodes - `python3 sim/simulator.py validate`),
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

**3.5 There is no save-format migration, ever. Stop designing for one.**
A decision, not an oversight. A game is about half an hour, nobody is forced
to update, and anyone running one stays on the version they started on. A save
written by an old build does not have to load in a new one.

So: rename a persisted field, drop one, change its units, restructure the
whole save. No shim, no version stamp, no upgrade path, no `if "old_key" in
data`. Every agent that has looked at this has independently invented a
migration plan for a problem this project does not have; do not be the next
one.

What this does NOT excuse: save/load still has to work *within* a build. The
suite exercises it hard, and with `--session` every single command is a save
followed by a load, so a field that fails to round-trip breaks the game in
normal play. `SAVE_FIELDS` still matters. Its *history* does not.

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

**The tree had no production side; `data/production/` is now it.** The tree
records what every process consumes and nothing about what anything produces,
which - not the existence of `prices.json` - is why every cost bottomed out in
a book value: there was no physical structure to compute one from.

`data/production/` covers **99.7% of consumption sites** (156 of 159
materials - `python3 sim/validate_production.py` for current coverage). Read
`data/production/_SCHEMA.md` before adding to it. The rule
that governs every number there: a yield is a physical fact - ore grade times
recovery, reaction stoichiometry, latent heat - and is NEVER derived from what
the material sells for, nor tuned so a computed price matches `prices.json`.
Those prices are 91.8% the author's own estimates and this data exists to
replace them.

    python3 sim/validate_production.py          errors and coverage
    python3 sim/validate_production.py --todo   what is still missing
    python3 sim/audit_costs.py                  where the cost base is

The remaining 0.3% is deliberate and recorded, and is now exactly the joint
byproducts: `germanium_g` and `indium_g`, two trace metals with no
independent ore, and `coal_tar_kg`. All three come out of another process and
have no key of their own, which is the same underdetermination
`Complaints/29` records - they cannot be priced from the cost side at all,
so an entry for them would be an invention, not a gap.

**Nothing reads this data yet.** The price solver described in
`ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 2 is the next piece, and until it
exists the engine still uses `prices.json`. Coverage is not the same as
being wired in.

**Make the founder's mechanisms general enough that other actors can use
them**, rather than making the founder less detailed.

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
- **`id()` is an address, not an identity, and this project has already lost
  a day to that.** Two caches keyed on `id(demand)` made the whole simulation
  non-deterministic: CPython hands a freed object's address to the next
  same-sized allocation, so a later tick's Counter landed where a dead one had
  and the cache replayed a stale answer under a fresh year. An `id()` may be a
  dict key for speed; the entry must then hold the object itself and confirm
  the hit with `is`. `sim/tests/test_determinism.py` fails if anyone
  reintroduces the shape. Fixed and verified - the full story, including which
  hypotheses were wrong and why one probe produced a false negative, is in
  `Complaints/closed/27-nondeterministic-simulation.md`.
- **When you instrument a bug, the instrument is part of the experiment.**
  The probe that cleared the guilty cache built a comparison tuple on every
  call; its own allocations were exactly what stopped addresses being
  recycled, so it suppressed the effect it was measuring and reported the
  absence as evidence.
- **The tree tools write to the repository, and now only when asked.**
  `treetool.py merge|judge|repair|apply-caps` each rewrite a committed data
  file, and each now reports by default and writes nothing. `--write` is what
  commits the result.

  This bullet used to say "pass `--dry-run` if you only meant to look", and
  that was a rule protecting people who had already read it. Two agents wrote
  `data/judgement.json` by accident anyway, the second of them while running a
  read-only-sounding `judge` to compare output during an unrelated task. A
  flag you have to know about does not protect the person who does not know,
  so the default moved instead. `--dry-run` is still accepted and is now a
  no-op, because it is written into scripts and into these instructions and
  every caller using it was asking for what already happens.
- **`Sim` is one god object.** Every mixin method talks through `self`, so
  the coupling is real however the files are arranged. A full decomposition
  has been considered and rejected, with reasons, in `sim/ARCHITECTURE.md` -
  do not silently restart it.

  For the attribute and method counts, run the scripts in that file's
  "runtime graph is one god object" section. **They are deliberately not
  repeated here.** This bullet used to carry them, and every one went stale
  the next time somebody split a mixin, because a figure quoted in two
  places drifts in one of them and nothing notices. A number belongs next to
  the script that produces it, in one file, and everywhere else points.
- **Much of the engine is majority comment, and the comments are
  load-bearing.** They are how agents hand each other the reason a thing is
  the way it is. Do not strip them to "clean up".

  How many of the largest files are majority comment depends on whether a
  docstring counts as documentation or as code, and the answer differs under
  the two rules. `sim/ARCHITECTURE.md` states both rules, gives the script
  for each, and derives its own file list rather than hardcoding one. Run it
  rather than quoting a figure from here; this bullet held one and it was
  wrong within a fortnight.
- **`_internal` fields are for auditors, `note` fields are for players.**
  Never put an audit marker where a player will read it.

---

## 7. Naming

Identifiers two characters or shorter, measured three ways because the number
you quote depends on what you count:

    python3 sim/code_health.py --names

Say which of the three methods you mean when you quote a figure - the first
two attempts at this disagreed and both were right. `docs/architecture/
NAMING_PLAN.md` carries figures of its own that this command will not
reproduce, because `sim/` has grown from the 83 files that scan covered to
197 today (`find sim -name "*.py" | wc -l`) and
NAMING_PLAN.md's own account says the original scan's exact grammar is lost,
not merely uncommitted; treat NAMING_PLAN.md's numbers as historical and this
command's output as current. The scanner's detectors are tested against
fixtures in `sim/tests/test_code_health.py`.

**Three commands, and you need all three.** `code_health.py --names` gives
the burndown total. `.pylintrc` turns pylint into the worklist - every short
name it can see comes back as a `file:line` somebody can fix:

    python3 -m pylint sim/ | grep -c C0103

That reads 0 today, from 246 when the sweep started, **and a clean pylint is
not a tree without short names.** Pylint's `invalid-name` check is driven by
how pylint CLASSIFIES a binding, and three classifications carry no name
check at all: a module-level name bound to a CALL (`KB = os.path.join(...)`
is invisible while `QQ = 5` one line below is reported), a module-level loop
target, and a lambda parameter. Measured:

    python3 sim/pylint_blind_spots.py
    461   (module-level assignments 254, lambda parameters 117,
           module-level loop targets 90)

which is nearly twice what pylint found in the first place, because this
codebase keeps most of its short names exactly where pylint is quietest -
the test suite is written as module-level script code rather than as
functions. Use pylint for the worklist and that script for what the worklist
cannot see. Neither number is the whole problem on its own.

This is the single biggest obstacle to anyone reading this code, and it gets
worse every time someone adds to it.

**The rule for new and edited code:** spell names out. The only acceptable
short names are `i` as a loop index, and `x`/`y` as coordinates, and only
inside a scope short enough to see whole. Everything else gets a word:
`node`, `node_id`, `sim`, `trade`, `material`, `rate`, `key`, `total`.

**This applies to prose, docstrings and design documents, and it is the rule
most often broken.** `p = A'p + w.l + rents` is four letters standing for
four things nobody can recover without the textbook. So is

    q_i = gamma_i + (beta_i / p_i) * (Y - sum_j p_j * gamma_j)

which is a real line that went into `sim/world/demand.py`, past a PM who
quoted it back approvingly, in the same week this paragraph was written. A
reader with no economics has no way to tell that from a radiation equation.
Write it out:

    quantity_of(good) = subsistence_floor_of(good)
                      + marginal_budget_share_of(good) / price_of(good)
                        * (income - cost_of_all_subsistence_floors)

Longer, and it can be read once by someone who has never seen a demand
system. If the standard name for a thing is a Greek letter, say what it
means in words on first use and then use the words. Citing the textbook
name is fine - "this is the Stone-Geary form" - as a POINTER, never as the
explanation.

**Fix bad names you pass through, where it is cheap.** If you are editing a
function and it has a one-letter local whose meaning you have just had to
work out, rename it while you are there - you have already paid the
expensive part, which is understanding it. Two limits: never rename in a
commit whose diff you need someone to read for a different reason, and
never rename a parameter without checking every call site by hand, because
`prove_rename_safe.py` cannot cover those. If it is not cheap, leave it and
say so.

A sweep is planned; see `docs/architecture/NAMING_PLAN.md` for the tiering,
the per-name meanings and the tooling. `python3 sim/code_health.py --names`
prints today's Tier-1 share; quote that, not NAMING_PLAN.md's, for current
state. Tier 1 is a purely local variable, provably safe to rename; a
function PARAMETER is Tier 2, because `prove_rename_safe.py` cannot cover a
caller passing by keyword.

Only five names (`v`, `i`, `_k`, `_y`, `l`) mean one thing everywhere; most
vary by site (`q` is a function, a quantity, a quality score and a price
quote in four different places), so there is no global find-and-replace for
them.

`python3 sim/prove_rename_safe.py <ref>` proves a rename changed nothing but
names, by comparing compiled bytecode: a local's name is not in `co_code`, so
a pure local rename leaves the executed bytes identical, while an attribute or
global moves `co_names` and a literal moves `co_consts`. That is a proof over
every possible run rather than a sample of nine, and it does not depend on
`perf_fingerprint` working.

**It has two holes, and both report as a failure rather than a proof.** A
reported failure on a rename commit is therefore not automatically a bug;
read which hole it is before believing it.

1. **A parameter passed by keyword.** The caller's `name=` breaks invisibly,
   because the caller still compiles. Use `rope`, which updates keyword call
   sites across files; it was tested on exactly this and got them right.
2. **An ANNOTATED parameter.** A parameter carrying a PEP 484 annotation has
   its NAME stored as a string constant in the ENCLOSING scope, for
   `__annotations__`. So renaming `def f(k: str)` to `def f(node_id: str)`
   moves the enclosing module's `co_consts` although nothing was edited but
   the name, and the tool reports "a CONSTANT changed" as if a docstring had
   been touched. Verified: two modules differing only in that name compile to
   enclosing `co_consts` of `('k', 'return')` and `('node_id', 'return')`;
   drop the annotation and both are empty. **This hole widens every time
   annotations spread further through the engine**, so expect it more often,
   not less.

The tool prints which constants moved, which tells the two apart at a glance:
a pair of bare identifiers (`gone: 'k' / added: 'node_id'`) is the annotation
hole, a sentence is a real prose edit that belongs in its own commit.

The tech-tree DATA schema fields (`lab`, `mat`, `cap`, `rev`, `up`, `ph`,
`sch`, `art`, `sus`, `gov`, `conf`, `pre`, `yrs`, `kb`) are a separate job,
and a cheaper one than it looks. Measured: **739 read sites across 13 files**
(no command reproduces this figure today; it is not scripted anywhere in the
repo, so treat it the same as the naming counts above, unverifiable until
someone commits the scan), plus the **2,864 nodes**
(`python3 sim/simulator.py validate`) and the branch sources
(`ls data/branches/*.json | wc -l`; this line said 39 while that command
answered 40, which is the one failure mode worse than an unverifiable
number - a figure with its own refutation printed beside it). No save
migration is needed at all - saves store node ids, never node records - and
the JSON protocol already translates these to readable keys on the way out
(`n["ph"]` becomes `"founder_hours_total"`), so nothing on the wire changes.
One real collision: `gov` is both a per-node field and a `Sim` attribute in
`SAVE_FIELDS`. Two renames, not one.

---

## 8. Working habits this repo expects

- Every discovered bug becomes a regression test with the smallest scenario
  that reproduces it. See `Complaints/` and `sim/tests/`.
- Every number asserted in a prose document must have been computed by the
  simulator. Prose quotes the data; it never asserts it.
- Claims about the codebase should be measured, not remembered. If you change
  the shape of the code, re-measure the counts in `sim/ARCHITECTURE.md`.
- **Standing rule, added after the stakeholder flagged documentation going
  stale silently: a number in prose carries the command or script that
  produced it, right next to the number, or it does not go in.** This file
  has already shipped wrong node counts and wrong file counts that nobody
  caught because nothing next to the number said how to check it. Where a
  command genuinely does not exist yet (a throwaway scan that was never
  committed, for instance), say so explicitly in the same sentence instead
  of leaving the number to look authoritative. A number with neither a
  command nor an "unverifiable" label next to it is a bug in this file.
