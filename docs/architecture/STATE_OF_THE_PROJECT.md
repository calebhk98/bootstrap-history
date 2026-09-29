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
| 3 | the household extraction | Done: `sim/engine/actors/household.py`. Further actor types (firm, state, other player) do not exist yet. |
| 4 | food and people | Wired: agriculture and demography run through the engine's yearly demographic step, with a persistent granary and weather pooling. See `WIRING_MILESTONE_4.md`. |
| 5 | the wage and the price solve | Both halves have mechanisms. The engine's live wage is built from cost-of-living factors; the live material price table is still the book file unless `use_solved_prices` is passed to `sim/engine/data.py:load`, which is off by default. The exit checklist is `Complaints/123`. |
| 5b | when a technique exists (era gate) | Built; every technique states what it needs and when, and the solver refuses techniques that cannot reach a needed temperature. Coverage: `validate_production.py`. |
| 6+ | transport, settlements, state finance, war | Transport is wired into freight cost. Military logistics is wired into state pressure. Settlements, state finance and war have no dedicated module (`Complaints/109`, `Complaints/111`). |

## What is not built or not linked

Re-check each with the grep above before trusting it; several of these have
changed hands since this file was first written.

- **Solved prices are not the default.** The switch is per call, not per
  material. The migration is to graduate materials out of the book file one
  family at a time and end with deleting it; `Complaints/123` is that
  checklist. Blockers named there and in `Complaints/43`: rent for
  non-ore extraction, a structured land-area field on grown goods in
  `data/production/`, and a policy for era-unreachable goods (unavailable or
  an import price).
- **Joint products.** `sim/world/demand.py` computes value-share splits;
  `Complaints/29` records how far the solver uses them.
- **Labour market.** `sim/world/labour_market.py` is used by the yearly farm
  workforce step. Whether wages and non-farm trades read it is the open part
  (`Complaints/45`).
- **Hardcoded outcomes.** `python3 sim/constants.py --burndown` names them.
  The mine-capex family has a recorded fix: derive it from the deposit
  model's sinking cost (`Complaints/37`).

## What to do next, in order

Ordered by what each item unblocks, not by ease.

1. **Finish the labour-market wiring** so a famine or a wage shock moves
   people between trades, not only the farm workforce (`Complaints/45`).
2. **Use value-share joint allocation everywhere the solver splits joint
   outputs**, and verify against the silver-and-lead reversal (`Complaints/29`).
3. **Add a structured land-area field to `data/production/`** for every grown
   or land-limited material. It is the blocker for Malthusian land pressure
   reaching any price a player pays (`Complaints/43`).
4. **Extend rent to the non-ore extracted materials** (forest, quarry,
   salt-pan, gold's placer step) with the same shape `deposits.py` has for ore.
5. **Graduate materials out of the book price file one at a time**, starting
   with manufactured goods with no extracted input upstream, before touching
   the global switch (`Complaints/123`).
6. **Continue the constants burndown**, starting with the mine-capex family,
   and re-audit the engine modules that were mid-edit when the audit was
   filed (`Complaints/37`).
7. **Review the branch-authored values that were held back** from the tree
   merge (`Complaints/30`, closed; the held-back list is recorded there).
8. **Re-tiling regions can wait**; the intensive-margin rent closed the acute
   symptom (`Complaints/46`).
9. **The naming sweep and the tree field rename** remain queued and low
   priority: readability only, proven safe by `prove_rename_safe.py`
   (`NAMING_PLAN.md`).

Items 1 to 2 are wiring jobs against modules that already exist; 3 to 5
decide whether "prices are calculated, not looked up" reaches a real game;
6 to 7 are debt paydown; 8 to 9 are real but not urgent.
