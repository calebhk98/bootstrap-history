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
| 3 | actors | `Actor` base with `Household`, `Government` and `Firm` in `sim/agents/` (see `ACTORS.md`). Governments and firms imitate founder inventions, enter where demand is unmet and share one labour pool and goods market with everyone else (`Complaints/103` for what remains). |
| 4 | food and people | Wired: agriculture and demography run through the engine's yearly demographic step, with a persistent granary and weather pooling. See `WIRING_MILESTONE_4.md`. |
| 5 | the wage and the price solve | The solver gives every good a cost of making; the book file is deleted. On the default agent economy wages, prices and the interest rate are the year's market clearing, and money is a stock held in accounts, struck from each civilisation's coin metal. Node revenue is derived from output for nodes that make something; the rest is in `Complaints/140`. |
| 5c | the agent economy | The default economy (`sim/economy/`, described in `ECONOMY_AGENTS.md`): households, producers, merchants, a lender pool, a mint and the state, with every market clearing each year. The engine reaches it only through `sim/engine/economy_port*.py`. Measure: `python3 -m sim.tests --list` for the economy topics, `python3 sim/constants.py --kind temporary_heuristic` for its declared shortcuts. |
| 5b | when a technique exists (era gate) | Built; every technique states what it needs and when, and the solver refuses techniques that cannot reach a needed temperature. Coverage: `python3 sim/simulator.py validate`. |
| 6+ | transport, settlements, state finance, war | Transport is wired into freight cost and into market areas on the tile map. Military logistics is wired into state pressure. The state raises and spends money in the same markets and covers a deficit by borrowing, issuing or debasing. War has no dedicated module (list what is open with the status grep below). |

## What is not built or not linked

Each point names the issue that tracks it; read its status line before acting.

- **Build-decision prices.** Market prices are the year's clearing on the
  agent economy, but the engine's project costs still amortise from solved
  costs (`Complaints/135`).
- **Node revenue.** Revenue is derived from output for nodes that make
  something; the remainder is authored and capped against solved cost
  (`Complaints/140`).
- **Civilisation units.** Engine code does not name a civilisation (pinned by
  `sim/tests/test_civilisation_independence.py`), but some internal money
  and land are still the book's Roman units (`Complaints/140`).
- **Regions as a view of tiles.** Land, forest, deposits and weather read
  tiles; reach, freight and mineral tables still read a region's anchor
  point (`Complaints/136`).
- **Deeper capital markets and other countries as full economies.** A pooled
  household-funded credit market exists; banks, bonds, equity and insurance
  do not, and partners trade as external sellers and buyers rather than as
  economies (`Complaints/106`, `ECONOMY_AGENTS.md`).
- **Legacy postings.** Engine postings without a named payer or payee are
  booked against `edge:legacy`; the share should fall to zero
  (`Complaints/382`).

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
next playtest until most open and partly fixed issues are done and the
first roadmap items below are built; the mod system may wait. The roadmap
is the long pole, so it runs first and the defects below fill the agents it
leaves free. What is left, in order:

1. **Defects and data errors**: every open or partly issue that is a
   defect rather than a request (`Complaints/README.md` says how issues are
   classed).
2. **Duplicated structures**: replace the region layer with the tile map
   (`136`).
3. **Screens the player lacks** and **scale tools and requests**: the
   remaining open requests in `Complaints/`.
4. **The roadmap** below.

`grep -l '^\*\*Status:\*\* \(open\|partly\)' Complaints/*.md` lists what
is still to do.

## Roadmap, in order

Ordered by what each item unblocks. Decisions on the roadmap issues are in
their status lines; `grep -m1 '^\*\*Status' Complaints/*.md` lists everything.

1. **Finish the tile map** (`Complaints/136`): retire the region anchor for
   reach, freight and mineral tables.
2. **Finish actors** (`Complaints/103`, `106`, `110`): firm choices (license,
   publish, keep secret), deeper capital markets, interest groups, and other
   countries as full economies and players (`sim/agents/MULTIPLAYER.md`).
3. **Money in physical units** (`Complaints/140`) and the legacy postings
   (`Complaints/382`).
4. **Model gaps**: actions and builds that are modelled as research, trade
   reach from transport, non-grain food, domain growth replacing the generic
   multiplier (`Complaints/112`).
5. **Mod system** (`mods/TASKS.md`) and the remaining hardcoded outcomes
   (`python3 sim/constants.py --burndown`).

Parked on purpose: issues with status `pinned`
(`grep -l '^\*\*Status:\*\* pinned' Complaints/*.md`).
