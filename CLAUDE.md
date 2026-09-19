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

`docs/architecture/` holds four documents; read its README first. The live
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
materials; re-measured after three `conf: D` entries were deleted rather
than kept). Read `data/production/_SCHEMA.md` before adding to it. The rule
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
python3 sim/treetool.py judge --dry-run    # judge nodes in isolation
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
- **The tree tools write to the repository.** `treetool.py merge|judge|repair|
  apply-caps` each rewrite a committed data file. Pass `--dry-run` if you only
  meant to look.
- **`Sim` is one god object.** This line used to quote **165** instance
  attributes CARRIED (a scan of `__init__` missing 8 reached only as `s.X`
  from `proto/` and 3 hidden behind `self.__dict__[...]`). SUPERSEDED, and
  deliberately not replaced with a corrected number:
  `sim/ARCHITECTURE.md`'s "runtime graph is one god object" section states,
  in its own voice, that the demography wiring deleted `pop_deficit` and
  `_pop_recovery_years` and turned `pop_scale` and `wage_index` into
  computed properties, which makes 165 stale, and that the counting method
  behind 165 was only ever described in
  `docs/architecture/SIM_STATE_INVENTORY.md`, never scripted, so nobody can
  re-derive today's true figure from it. Treat 165 as unverifiable; do not
  quote it as current, and do not invent a replacement by arithmetic on it.
  What IS current and scripted: `Sim.__init__` still assigns **44** instance
  attributes - unchanged by the 2026-09-18 split below, which touched
  `step()`, not `__init__` - and `Sim` and its mixins now have **538**
  methods between them, all talking through `self`.
  `sim/ARCHITECTURE.md`'s same section gives the script for both numbers,
  right next to where it quotes them. The 538 supersedes the 524 this line
  carried until 2026-09-18: `economy.py` (6,570 lines) split into a 598-line
  `EconomyMixin` composition point over `MarketMixin`, `CreditMixin`,
  `MiningMixin` and `ProductionMixin` in their own files, and `society.py`
  (3,802 lines) split the same way into a 45-line `SocietyMixin` over
  `HazardsMixin`, `StatePressureMixin`, `AdoptionMixin` and `DiffusionMixin`.
  `Sim`'s own base list in `core.py` did not change - see
  "the composition-point pattern" in `sim/ARCHITECTURE.md` for why that was
  the point. Breakdown: `Sim` 246, `EconomyMixin`-and-its-four 121,
  `SocietyMixin`-and-its-four 61, `LabourMixin` 50, `ProjectsMixin` 46,
  `FogMixin` 8, `GeographyMixin` 6 (same script, updated to walk into the
  sub-mixins - the old script, unmodified, now silently undercounts at 366,
  because it cannot see methods a composition point inherits rather than
  defines). The whole +14 over 524 is `Sim`'s own: `step()` was a
  1,760-line method and is now a 42-line dispatcher over 14 `_step_*` phase
  methods. A full decomposition of the god object itself has been
  considered and rejected with reasons in `sim/ARCHITECTURE.md`. Do not
  silently restart it.
- **Much of the engine is majority comment, and the comments are
  load-bearing.** They are how agents hand each other the reason a thing is
  the way it is. Do not strip them to "clean up". (The old "five of eight"
  figure was stale and, worse, unreproducible - it never recorded whether a
  docstring counted as comment or code. Re-measured 2026-09-18 with BOTH
  rules scripted: it is **one of eight** counting docstrings as
  documentation - core.py, now 55% (was 54% before the split; core.py grew
  from 4,577 to 4,929 lines, the growth mostly comments explaining what the
  `step()` split moved and why) - and **zero of eight** counting them as
  code. The "eight" is no longer the same eight files: `economy.py` and
  `society.py` shrank to composition-point shims and dropped out, replaced
  in the comparison by the largest files that now exist, `economy_market.py`
  and `cli_interactive.py` among them - see `sim/ARCHITECTURE.md` for the
  full successor list and why it is the fair comparison. That supersedes
  the four-and-one this line carried, and the direction matters: the files
  that stayed large got denser, not better documented.
  `sim/ARCHITECTURE.md` states both rules and gives the script for each.)
- **`_internal` fields are for auditors, `note` fields are for players.**
  Never put an audit marker where a player will read it.

---

## 7. Naming

Identifiers two characters or shorter, measured three ways because the number
you quote depends on what you count. **There is now a command, and this
paragraph no longer quotes a figure of its own:**

    python3 sim/code_health.py --names

This paragraph used to assert 4,972 occurrences, 3,813 binding sites, 3,759
name-per-scope, 176 to 332 distinct names, 72 of 83 files, `k` at 568 across
53 files, and a 72.4% Tier-1 share, and to say in the same breath that none
of them carried a command, because `docs/architecture/NAMING_PLAN.md`'s
scanner "is not part of this repo; it is a throwaway analysis script, not a
shipped tool." That condition has been met: the scanner is committed as
`sim/code_health.py`, with its detectors tested against fixtures in
`sim/tests/test_code_health.py`.

**Not one of the seven reproduces.** Run the command and it says so, per
figure, in its own output. What it does NOT say, and what you should not
conclude, is that the old numbers were wrong: `sim/` has grown from 83 files
to 194 since that scan, the worst offenders it named have been decomposed,
and NAMING_PLAN.md's own account says the original scan's exact grammar is
lost rather than merely uncommitted. So the two are not measuring the same
tree by the same rule, and the gap cannot be attributed. The scanner reports
binding sites as unreproducible for exactly this reason, rather than
inventing a definition and pretending to check it.

What replaces them is the command, run today, whenever you need a number.
Say which of the three methods you mean when you quote one, because the
first two attempts at this disagreed and both were right.

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
prints today's Tier-1 share alongside the 72.4% NAMING_PLAN.md recorded, and
says whether it reproduces; it does not, for the reasons above, so do not
quote either figure without running it. Tier 1 is a purely local variable,
provably safe to rename; a function PARAMETER is Tier 2, because
`prove_rename_safe.py` cannot cover a caller passing by keyword.

Only five names (`v`, `i`, `_k`, `_y`, `l`) mean one thing everywhere; most
vary by site (`q` is a function, a quantity, a quality score and a price
quote in four different places), so there is no global find-and-replace for
them.

`python3 sim/prove_rename_safe.py <ref>` proves a rename changed nothing but
names, by comparing compiled bytecode: a local's name is not in `co_code`, so
a pure local rename leaves the executed bytes identical, while an attribute or
global moves `co_names` and a literal moves `co_consts`. That is a proof over
every possible run rather than a sample of nine, and it does not depend on
`perf_fingerprint` working. It does NOT cover parameter renames, where a
caller passing by keyword breaks invisibly - it reports those separately.

The tech-tree DATA schema fields (`lab`, `mat`, `cap`, `rev`, `up`, `ph`,
`sch`, `art`, `sus`, `gov`, `conf`, `pre`, `yrs`, `kb`) are a separate job,
and a cheaper one than it looks. Measured: **739 read sites across 13 files**
(no command reproduces this figure today; it is not scripted anywhere in the
repo, so treat it the same as the naming counts above, unverifiable until
someone commits the scan), plus the **2,864 nodes**
(`python3 sim/simulator.py validate`) and the **39**
`data/branches/*.json` sources (`ls data/branches/*.json | wc -l`). No save
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
