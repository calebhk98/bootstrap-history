# State of the project

The stakeholder's standing questions: did we do all the milestones, is
everything in `Complaints/` finished, are all the systems built and linked.
This file answers them without keeping a copy of anything that can be
computed. Anything below that looks like a fact carries the command that
measures it; a claim with no command says so. Re-run before acting on it.

Read this file, then `ENDOGENOUS_COSTS_AND_DOMAINS.md` (the live plan).

## Issues

Not kept here. Every issue file in `Complaints/` (not finished) and
`Complaints/closed/` (finished) starts with a status line, and the table is
printed from those files:

    python3 sim/issue_status.py                 every issue: number, title, status, folder
    python3 sim/issue_status.py --status open   only one status
    python3 sim/issue_status.py --check         exits non-zero on a missing or invalid
                                                status line, or a status in the wrong folder

Statuses are `open`, `partly`, `pinned` and `closed`. `pinned` is a parked
state held on purpose by a regression test, not an unresolved bug. Playtest
and audit reports live in `Complaints/reports/`; standing design decisions
that are not defects are in `DESIGN_PRINCIPLES.md`. Closing an issue means
editing its status and moving the file to `closed/`; `--check` enforces both.

## Milestones

Measure with these; none of their output is copied here.

    python3 sim/simulator.py validate           the tree is a valid DAG and fully priced
    python3 sim/constants.py --burndown         declared numbers, temporary heuristics,
                                                named hardcoded outcomes (target: none)
    python3 sim/validate_production.py          production coverage and errors (--todo for gaps)
    python3 sim/audit_costs.py                  where the cost base comes from
    grep -rn "from sim.world import\|import sim.world" sim/engine sim/solve_prices*.py
                                                which domain modules the engine or solver import

| | milestone | state |
|---|---|---|
| 0 | the production side (`data/production/`) | Built and validated by `validate_production.py`. The remaining gaps are joint-byproduct materials that cannot be priced from the cost side (`Complaints/29`). |
| 1 | provenance and a burndown | Working. A rising count of declared heuristics means the audit is finding more, not that the project is regressing. |
| 2 | the synthetic world | Not started and not needed: domain models were built standalone under `sim/world/` and wired in afterwards. |
| 3 | actors | `Actor` base with `Household`, `Government` and `Firm` in `sim/engine/actors/` (see `ACTORS.md`). Governments and firms imitate founder inventions; firms do not yet compete for labour or inputs (`Complaints/107`). |
| 4 | food and people | Wired: agriculture and demography run through the engine's yearly demographic step, with a persistent granary and weather pooling. See `WIRING_MILESTONE_4.md`. |
| 5 | the wage and the price solve | Wages come from the labour market (subsistence floor, training premium, tightness), and money is anchored to each civilisation's coin metal; neither reads the book file. Material prices still start from the book with the solver filling gaps; the exit checklist is `Complaints/123`. |
| 5b | when a technique exists (era gate) | Built; every technique states what it needs and when, and the solver refuses techniques that cannot reach a needed temperature. Coverage: `validate_production.py`. |
| 6+ | transport, settlements, state finance, war | Transport is wired into freight cost. Military logistics is wired into state pressure. Settlements, state finance and war have no dedicated module (`Complaints/109`, `Complaints/111`). |

## What is not built or not linked

- **Market prices.** Prices are long-run production costs; there is no
  per-period market clearing stocks and current capacity, and money is not
  revalued when its coin metal floods or runs short (`Complaints/139`).
- **Closed demand loop.** What the founder or a firm produces does not reach
  the society's supply, so workers in that trade do not move away
  (`Complaints/106`).
- **Book material prices.** The solver fills only what the book lacks; some
  new materials cannot be priced yet (`python3 sim/simulator.py validate`
  warns about them) (`Complaints/123`).
- **Civilisation independence.** Engine code names civilisation ids and
  assumes Rome exists (`Complaints/135`, `Complaints/136`).
- **Two maps and a committed tree.** Regions and tiles coexist
  (`Complaints/140`); `data/tech_tree.json` duplicates the branches
  (`Complaints/141`).

## Playtest defects come before the roadmap

A playtest measures the game only if the game does what it says. Defects that
change which strategy wins, or make a run look rigged, are fixed before the
next round of playtests and before roadmap work whose effect those playtests
would measure. The rule used for every fix: where a screen shows a number and
the engine applies one, both come from one function.

The first tranche (money charged off the books, the fixed seed, the mortal
founder and the victory ending, content leaking between civilisations, text
that disagreed with the applied figure, unpreviewed spending, blocker
readouts) is in. What is left, in order:

1. **Finish the partly fixed ones.** Each has a "remains" paragraph:
   `128`, `129`, `208`, `214`, `220`, `227`, `231`, `240`, `244`, `249`,
   `256`, `260`, `263`, `265`.
2. **Losing the game or money without being told**: an interrupted
   multi-year step loses the run (`225`); a forgotten technology is rebuilt
   at full price (`237`); `stuck` recommends a concern `open` refuses
   (`219`).
3. **Staffing closures and alerts that drown in the step report**: `81`,
   `84`, `205`, `206`, `233`, `235`, `246`.
4. **Consequences stated without size or cause**: `216`, `241`, `242`,
   `245`, `247`.
5. **Search, grammar and small text** (`196`, `197`, `210`, `217`, `221`,
   `236`) and the review in `Complaints/35`, which still has to be split into
   issues.
6. **Requests** (`211` to `213`, `215`, `229`, `230`, `243`, `270` to `272`)
   wait behind the roadmap unless one blocks a playtest.

`python3 sim/issue_status.py --status open` and `--status partly` list what
is still to do.

## Roadmap, in order

Ordered by what each item unblocks. Decisions on the roadmap issues
(104-116) are in their status lines; `python3 sim/issue_status.py` lists
everything.

1. **Make every civilisation independent** (`Complaints/135`, `136`): no
   engine code names a civilisation, Rome is one data file, internal units
   are physical. Multiplayer and mods depend on it.
2. **Build the market** (`Complaints/139`, `106`): per-period clearing from
   stocks and every actor's production, sunk costs out of prices, money
   revalued from its coin metal. Then make solved prices the default and
   delete the book (`Complaints/123`).
3. **Finish actors** (`Complaints/107`): firms compete for labour and inputs,
   player choices (license, publish, keep secret). Then the state budget
   (`109`), capital markets (`110`), interest groups (`114`), and the
   international economy (`113`).
4. **Remove duplicated structures**: generate the tree from the branches
   (`Complaints/141`) and retire the region layer (`Complaints/140`).
5. **Money in physical units** (`Complaints/144`) and the silver cost check
   (`Complaints/143`).
6. **Model gaps**: actions and builds that are modelled as research
   (`Complaints/137`), trade reach from transport (`138`), non-grain food
   (`142`), domain growth replacing the generic multiplier (`104`, `116`).
7. **Mod system** (`mods/TASKS.md`) and the remaining hardcoded outcomes
   (`python3 sim/constants.py --burndown`).

On hold by decision: `Complaints/42`, `115`; intended as mods: `108`, `111`,
`112`.
