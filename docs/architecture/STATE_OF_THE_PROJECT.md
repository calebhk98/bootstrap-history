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
| 0 | the production side (`data/production/`) | Built and validated by `python3 sim/simulator.py validate`. The remaining gaps are joint-byproduct materials that cannot be priced from the cost side (`Complaints/29`). |
| 1 | provenance and a burndown | Working. A rising count of declared heuristics means the audit is finding more, not that the project is regressing. |
| 2 | the synthetic world | Not started and not needed: domain models were built standalone under `sim/world/` and wired in afterwards. |
| 3 | actors | `Actor` base with `Household`, `Government` and `Firm` in `sim/agents/` (see `ACTORS.md`). Governments and firms imitate founder inventions; firms do not yet compete for labour or inputs (`Complaints/103`). |
| 4 | food and people | Wired: agriculture and demography run through the engine's yearly demographic step, with a persistent granary and weather pooling. See `WIRING_MILESTONE_4.md`. |
| 5 | the wage and the price solve | Wages come from the labour market (subsistence floor, training premium, tightness), and money is anchored to each civilisation's coin metal; neither reads the book file. Every material price is solved; the book file is deleted. Authored node revenue is not yet derived from output everywhere (`Complaints/283`). |
| 5b | when a technique exists (era gate) | Built; every technique states what it needs and when, and the solver refuses techniques that cannot reach a needed temperature. Coverage: `python3 sim/simulator.py validate`. |
| 6+ | transport, settlements, state finance, war | Transport is wired into freight cost. Military logistics is wired into state pressure. Settlements, state finance and war have no dedicated module (`Complaints/105`, `Complaints/107`). |

## What is not built or not linked

- **Market prices.** Prices are long-run production costs; there is no
  per-period market clearing stocks and current capacity, and money is not
  revalued when its coin metal floods or runs short (`Complaints/135`).
- **Closed demand loop.** What the founder or a firm produces does not reach
  the society's supply, so workers in that trade do not move away
  (`Complaints/102`).
- **Node revenue.** Prices are all solved, but most nodes' revenue is still
  authored and capped against solved cost rather than derived from what they
  produce (`Complaints/283`, `Complaints/119`'s remains).
- **Civilisation units.** Engine code no longer names a civilisation, but
  internal money and land are still the book's Roman units
  (`Complaints/132`, `Complaints/140`).
- **Regions as a view of tiles.** Region land is summed from tiles, but
  reach and freight still read each region's hand-set anchor point
  (`Complaints/136`, `500`).

## Playtest defects come before the roadmap

A playtest measures the game only if the game does what it says. Defects that
change which strategy wins, or make a run look rigged, are fixed before the
next round of playtests and before roadmap work whose effect those playtests
would measure. The rule used for every fix: where a screen shows a number and
the engine applies one, both come from one function.

The first two tranches (money charged off the books, the fixed seed, the
mortal founder and the victory ending, content leaking between
civilisations, text that disagreed with the applied figure, unpreviewed
spending, blocker readouts, lost multi-year steps, staffing closures,
hazard and score screens, report noise) are in. The stakeholder holds the
next playtest until most open and partly fixed issues are done and roadmap
items 1 to 5 below are built; items 6 to 9 and the mod system may wait. The
roadmap is the long pole, so it runs first and the defects below fill the
agents it leaves free. What is left, in order:

1. **Defects and data errors**: `279` (coal as a smelting fuel before
   coke), `280` (option ids that name no node), `126` (audit markers in
   player notes), `68`, and the remains of `41`, `56`, `127`, `151`, `198`,
   `199`, `204`, `205`, `227`, `231`, `236`, `249`, `265`.
2. **Duplicated structures**: replace the region layer with the tile map
   (`140`).
3. **Screens the player lacks**: `71`, `88`, `90`, `94`, `95`, `96`, `97`,
   `100`, `101`, `132`, `178`, `243`, `270`, `272`, and the remains of
   `81`, `99`, `102`.
4. **Scale tools and requests**: `75`, `76`, `93`, `124`, `180`, `194`,
   `211` to `213`, `215`, `271`, `273` to `278`.
5. **The roadmap** below, items 1 to 5 required before the next playtest.

`grep -l '^\*\*Status:\*\* \(open\|partly\)' Complaints/*.md` lists what
is still to do.

## Roadmap, in order

Ordered by what each item unblocks. Decisions on the roadmap issues
(104-116) are in their status lines; `grep -m1 '^\*\*Status' Complaints/*.md` lists
everything.

1. **Make every civilisation independent** (`Complaints/131`, `136`): no
   engine code names a civilisation, Rome is one data file, internal units
   are physical. Multiplayer and mods depend on it.
2. **Build the market** (`Complaints/135`, `106`): per-period clearing from
   stocks and every actor's production, sunk costs out of prices, money
   revalued from its coin metal. Then make solved prices the default and
   delete the book (`Complaints/119`).
3. **Finish actors** (`Complaints/103`): firms compete for labour and inputs,
   player choices (license, publish, keep secret). Then the state budget
   (`109`), capital markets (`110`), interest groups (`114`), and the
   international economy (`113`).
4. **Remove duplicated structures**: generate the tree from the branches
   (`Complaints/137`) and retire the region layer (`Complaints/136`).
5. **Money in physical units** (`Complaints/140`) and the silver cost check
   (`Complaints/139`).
6. **Model gaps**: actions and builds that are modelled as research
   (`Complaints/133`), trade reach from transport (`138`), non-grain food
   (`142`), domain growth replacing the generic multiplier (`104`, `116`).
7. **Mod system** (`mods/TASKS.md`) and the remaining hardcoded outcomes
   (`python3 sim/constants.py --burndown`).

On hold by decision: `Complaints/41`, `115`; intended as mods: `108`, `111`,
`112`.
