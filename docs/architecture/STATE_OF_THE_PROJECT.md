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
read from those files:

    grep -m1 '^\*\*Status' Complaints/*.md     every issue's status line

Statuses are `open`, `partly`, `pinned` and `closed`. `pinned` is a parked
state held on purpose by a regression test, not an unresolved bug. Playtest
and audit reports live in `Complaints/reports/`; standing design decisions
that are not defects are in `DESIGN_PRINCIPLES.md`. Closing an issue means
editing its status and moving the file to `closed/`.

## Milestones

Measure with these; none of their output is copied here.

    python3 sim/simulator.py validate           the tree is a valid DAG and fully priced
    python3 sim/constants.py --burndown         declared numbers, temporary heuristics,
                                                named hardcoded outcomes (target: none)
    grep -rn "from sim.world import\|import sim.world" sim/engine
                                                which domain modules the engine or solver import

| | milestone | state |
|---|---|---|
| 0 | the production side (`data/production/`) | Built and validated by `python3 sim/simulator.py validate`, which also lists the materials that have a production entry but no seller in reach of a start. |
| 1 | provenance and a burndown | Working. A rising count of declared heuristics means the audit is finding more, not that the project is regressing. |
| 2 | the synthetic world | Not started and not needed: domain models were built standalone under `sim/world/` and wired in afterwards. |
| 3 | actors | `Actor` base with `Household`, `Government` and `Firm` in `sim/agents/` (see `ACTORS.md`). Governments and firms imitate founder inventions, enter where demand is unmet and share one labour pool and goods market with everyone else (`Complaints/closed/103-add-independent-firms-imitation-entrepreneurship.md`). |
| 4 | food and people | Wired: agriculture and demography run through the engine's yearly demographic step, with a persistent granary and weather pooling. See `WIRING_MILESTONE_4.md`. |
| 5 | the wage and the price solve | The solver gives every good a cost of making; the book file is deleted. On the default agent economy wages, prices and the interest rate are the year's market clearing, and money is a stock held in accounts, struck from each civilisation's coin metal. A node earns only from the output of the entries that name it in `operated_by`; typed revenue is deleted (the REVENUE lines of `validate` count both kinds). |
| 5c | the agent economy | The default economy (`sim/economy/`, described in `ECONOMY_AGENTS.md`): households, producers, merchants, a lender pool, a mint and the state, with every market clearing each year. The engine reaches it only through `sim/engine/economy_port*.py`. Measure: `python3 -m sim.tests --list` for the economy topics, `python3 sim/constants.py --kind temporary_heuristic` for its declared shortcuts. |
| 5b | when a technique exists (era gate) | Built; every technique states what it needs and when, and the solver refuses techniques that cannot reach a needed temperature. Coverage: `python3 sim/simulator.py validate`. |
| 6+ | transport, settlements, state finance, war | Transport is wired into freight cost and into market areas on the tile map. Military logistics is wired into state pressure. The state raises and spends money in the same markets and covers a deficit by borrowing, issuing or debasing. War has no dedicated module (list what is open with the status grep below). |

## What is not built or not linked

Each point names the issue that tracks it; read its status line before acting.

- **Node earnings.** Most nodes make no product and so earn nothing from
  output; whether a concern's takings follow the techniques in use is
  `Complaints/369`, and every entry an output-earning node runs states a plant (closed, `Complaints/closed/335`).
- **Deeper capital markets.** A pooled
  household-funded credit market exists; banks, bonds, equity and insurance
  do not (`Complaints/106`).
- **Disease.** `sim/disease/` is wired into `step_year` for the Mexica start
  (`sim/engine/disease_port.py`): the nation is one patch of three age bands and
  pathogens arrive by a labelled contact heuristic. Other civilisations still
  use authored staff_loss plagues; care collapse and density are open
  (`Complaints/471`).

## Order of work

The stakeholder holds the next playtest until most open and partly fixed
issues are done. The rule for every defect fix: where a screen shows a number
and the engine applies one, both come from one function. What is left, in order:

1. **Defects and data errors**: every open or partly issue whose title names
   something the game gets wrong.
2. **Requests**: the remaining open requests, after the owner decisions in
   their status lines and bodies (several say "wait" or "lower priority").
3. **Finish actors** (`Complaints/106`, `110`): deeper capital markets and
   interest groups.
4. **Mod system** (`mods/TASKS.md`) and the remaining hardcoded outcomes
   (`python3 sim/constants.py --burndown`).
5. **The fantasy equipment mod** (`Complaints/469`), last, as an acceptance
   test that a mod's goods price themselves.

`grep -l '^\*\*Status:\*\* \(open\|partly\)' Complaints/*.md` lists what
is still to do.

## Where the economy work stands

The accounting defects an outside review found are fixed (546, 547, 548 closed; 529 closed), and several
mechanisms moved toward physical inputs (513, 517, 531, 532, 534, 535, 550, 552, 559, 560 partly). What blocks
the rest is the opening: the hidden spin-up drifts for decades (473), and every change elsewhere moves where it
stops, so price and volume checks that read a particular year flip with unrelated merges. In order:

1. **The opening (526, with 473, 527, 545).** Households' savings wish has almost nothing to absorb it at the
   opening, so the opening's income falls toward the floors and the wage drifts down through the spin-up
   (526 "Measured cause"). The opening finding its own interest rate is the step in progress; saving with an
   asset to buy is land titles (538). 545 (own-plot food in the opening) can land only with 526: alone it drives
   the settled income toward nothing (branch `fix-545-opening-grows-its-own`).
2. **Regenerate the shipped openings after the opening is fixed, not before** (owner decision): they are stale,
   so a new game computes its own spin-up, and the topics that read full-length openings fail on time until
   `python3 sim/simulator.py openings --prune` ships them (557, and the 40-year money trace
   `spin_up_money_supply` keys).
3. **The slow topics still failing**, each with its cause in 558: tin against copper (511), bronze's early
   scarcity price, the Norse money regime, printed money reaching prices, the partner's glut cycle (553).
   Measure with `python3 -m sim.tests --slow --timing`.
4. **A year's cost (497)**: flat profile; the next cuts are model changes (fewer agents) or compiled clearing.

Rules this work kept, for whoever picks it up:

- A topic over the runner's limit fails; there is no per-topic allowance.
- When a merge breaks a check, first run it on `origin/main`, then bisect the first-parent merges
  (`git log --first-parent --oneline origin/main..HEAD`). Change a fixture only to keep its subject (an
  "equally visible" taxpayer, a baseline measured the same way in both worlds), never to find a window, a good
  or a bound that happens to pass; a check that fails for a real dynamic stays failing with its cause recorded.
- Speed changes must leave a stepped game's save byte-identical (sorted keys), with the CPU saving measured.
- Facts recalled rather than read are marked as such in the data's source fields; check them before relying
  on them. Parked on purpose: issues with status `pinned`
(`grep -l '^\*\*Status:\*\* pinned' Complaints/*.md`).
