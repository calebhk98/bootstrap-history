# Prototype gate: the ledger, living stock and project starting

**Status:** decided 2026-10-26 - go, with the changes in section 3 made before the next modules move. Task 2.4 of
`MODULE_MIGRATION_TASKS.md`.

## 1. What was moved, and the proof

| Prototype | Package | Views published | Commands applied | Reads declared | Mixins out of `Sim` |
|---|---|---|---|---|---|
| Ledger (money and stock changes) | `sim/ledger/` | 2 | 4 (+ `NoteSpend`, applied by the bridge) | 5 `legacy_*` | none (its owner's state has not moved) |
| Living stock and defence stores | `sim/living_stock/`, `sim/defence_stores/` | 10 | 5 | 31, from 14 owners | 8, replaced by one forwarder mixin |
| Project starting | `sim/projects/` | 6 | 4 | 64, from 15 owners | 3, replaced by two |

Counts are from the agents' reports and the specs; re-count with
`python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine import game_assembly as g; a=g.build(None, True); print(len(a.views), len(a.handlers))"`
and `tools/done_check.sh` (bases, MRO, cross-class references).

Proof for each step: the micro equivalence tier identical to the base (`python3 -m sim.tests.equiv check
docs/architecture/baseline/micro.json --tier micro`), the protocol golden transcripts identical, the quick tier
green. The one divergence met (Complaint 681, a real double count in the base) is kept on purpose behind a named
flag, so the chain of proofs stays unbroken; it is fixed in phase 9. Speed: the project-starting agent measured the
start gate and the year step on base and branch and found no measurable difference.

## 2. What the prototypes showed

1. **The shape holds.** Every rule moved became a plain function of plain values, tested without a game; every
   cross-topic write became a command; nothing in a moved module imports the engine.
2. **The read limit was the wrong gate.** A hub reads many facts (project starting reads 64 views); what keeps it
   testable is that each rule takes plain values. The 15-read stop criterion is dropped. What is watched instead:
   whether a module's views answer questions (several old names behind one view) rather than mirror methods, and
   whether any view had to be shaped to one caller.
3. **The first publisher of a view fixes its name and shape.** Both prototypes bridged `year`, `tree`,
   `is_venture` and `staff` under one name with two shapes, and both invented a `ChangeStanding` command that meant
   different things. Assembly refused the doubled names at once, so the collision cost a merge, not a bug.
4. **Nothing can be cached yet.** A view is cached only when every writer of what it reads goes through its owner's
   commands; while most state is written by unmoved code, nearly every view is `cached=False`. The speed benefit of
   views comes at the end of the migration, not during it.
5. **Shared year phases must be split first.** `seat_work` ran steps of five topics; project starting split it into
   named phases in the old order.
6. **Shipped modules need to contribute to extension points.** Only mods could provide; the 21 start checks could
   not become contributions of the modules that own what they check.
7. **Reads that write were found in every prototype** (lazy creation, a labour press inside a quote, a cast seeded
   on first read). Each was split into a read and a command in the old order; the equivalence check proved it.
8. **Command answers need a convention.** Handlers answer a value or a `Refusal`; a refusal is a truthy string.

## 3. Changes made before the next modules move

- Views more than one module reads live in `sim/engine/bridge_shared.py`, one entry each; the guide says to search
  for an existing view before adding one (`MODULE_MIGRATION_GUIDE.md`).
- A command lives with its owner, in `sim/<owner>/commands.py`, even before the owner moves (`sim/polity/`,
  `sim/workforce/` and `sim/foreign_trade/` exist this way now).
- `ModuleSpec.provides` and `Provision`: a shipped module answers an extension point, and a mod withdraws a shipped
  answer by `<module_id>.<name>` (`Operations.withdrawn`, `api.withdraw`).
- The guide adds: split a shared phase before moving its parts; a module partly moved reads its own unmoved parts
  through the bridge under its own names; handlers answer a value or a `Refusal`.

## 4. Order from here

From the catalogue's proposal (`catalogue/README.md`), re-measured before each batch, two or three agents at a time
on disjoint files:

1. Leaves: campaigns, stores, freight, agriculture, resources, foreign trade, coin, diffusion, mechanics, knowledge.
2. Middle: hazards, seats, polity, actors, prices, materials.
3. Walled packages as modules: workforce (labour), land (geography), markets (economy), disease.
4. Hub: finance, production, ventures, the rest of projects; then the ledger and reporting take their state, and
   the bridge's `legacy_*` views go.

Each module converts its own log writes to the reporting module's `RecordEvent` and its own money and stock writes
to the ledger's commands as it moves, rather than in one sweep across every file.
