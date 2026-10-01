# Add dedicated Education and Demography screens

**Status:** partly - `education` and `demography` exist; remains listed below

These systems are fundamental to civilization development but their information is scattered across generic screens and require triangulation.

## Education screen should include

- actual general literacy and elite literacy
- schooling ceiling
- annual schooling flow / school productivity
- school and academy units with operating status
- printing boost to diffusion
- agricultural labor release effect
- specialist/literate labor pool and its growth
- recent literacy changes and their causes
- path to goal if goal is literacy-related

## Demography screen should include

- total population and age cohorts
- birth rate and death rate
- disease burden and recent epidemics
- food/nutrition pressure on survival
- recent population shocks
- working-age population change
- wage pressure and labor consequences
- recovery trajectory and timeline

## Why it matters

Literacy and population are central to the game's loop: literacy affects economic productivity, education capacity, and state notice; population affects labor supply, disease burden, food requirements, and military capacity. These systems are too important to require triangulating several generic screens.

## Where it lives

Likely new screens in `sim/engine/proto/render_screens_big.py` or similar, with data from `sim/engine/society.py`, `sim/engine/core.py`, and literacy/population subsystems.

**Confidence:** Design recommendation

Also reported (Han China 100 AD fog playtest, tester item(s) 28, 73, 210; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the tester needed `state`, `money`, `values`, `population` and `score` to assemble goal progress; general literacy appears only as a raw fraction (0.06) on `score`, elite and general literacy are easy to confuse (elite 99 percent while general stayed at 6 percent for about 70 years), and there is no consolidated view of the chosen secondary goals, reserve target and open or closed institutions. Reproduces: yes (`score` shows the raw value).

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): `score` showed literacy as 0.75 while the literacy milestone read BLOCKED; a threshold milestone should print the exact figure against the requirement (for example 74.96% of 75.00%). Probably rounding, not a logic error. Reproduces: untested (needs a late game).

## Done

- `education` (aliases `literacy`, `schools`, `schooling`): general and elite literacy with ceiling, exact share of ceiling and next year's value, the schooling flow (new `effective_schooling_flow`, shared with the yearly literacy step), printing's boost, schooling nodes, literate-trade pools, trade schools and trainees.
- `demography` (took the alias from `population`): cohorts, last year's births and deaths and nutrition ratio, disease burden, epidemics under way, wage index and the trades. Replies list what the model does not hold.

## What remains

- Literacy and `score` still print the raw fraction; the milestone line does not show the exact figure against its requirement (the `education` screen does).
- No consolidated view of secondary goals, reserve target and open or closed institutions.
- No recovery trajectory or recent-shock history (only the last step is held); no per-school enrolment or cause of a literacy change.
- Births and deaths are not saved, so a freshly loaded session shows none until the next step.
