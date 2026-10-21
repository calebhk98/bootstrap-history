# The leisure preference and the hours elasticity are declared, not sourced

**Status:** open - `households_hours_offered.LEISURE_ELASTICITY` is a labelled heuristic; the anchor wage is solved at the opening from the hours the opening's runs hire, so how much leisure a trade has at the opening is a residual, not a measurement

Part of 473 (the opening is a point on a cycle), 608.

**What is wrong.** A household's hours that the plot and household work do not take are shared between leisure and the market by `leisure_hours_kept`: a share that falls smoothly as the wage rises, one half at an anchor wage. Two figures stand behind it:

- the elasticity of hours sold to the wage (`LEISURE_ELASTICITY`, confidence D, no source opened);
- the anchor wage of each trade, which `opening_leisure.seed` solves so that the hours households sell at the opening wage equal the hours the opening's producers hire. Whatever the plot, household work and sale do not use is therefore leisure at the opening, including unmodelled time (seasonal slack, sickness, travel, ceremony, a day of rest). Rome offers about 2000 hours a worker against what its recipes hire, so most of its year is leisure by this reading.

**Why it matters.** The opening is sized so offered equals hired (Eurace initialisation; Caiani et al. 2016), which is the right resting state, but the split between leisure and unmodelled time is not a finding, and the elasticity sets how far the wage moves when hours and demand differ.

**What it would take.** A source for hours worked in a pre-industrial year (time-use or budget studies; de Vries 2008, The Industrious Revolution, on household time allocation) and for the response of hours to wages; household work (645) taking its measured share before leisure; then the anchor derived from a utility of leisure with the opening's offered equal to hired as a check, not a fit.

**Test.** A figure for the elasticity with a cited source, and `python3 sim/constants.py --burndown` no longer listing `LEISURE_ELASTICITY`.
