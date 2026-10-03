# Validation seeds share one spin-up, so a median over seeds is one draw

**Status:** open

`python3 sim/economy_validate.py --seeds 1,2,...` plays each civilisation from the agent economy's hidden spin-up, which is cached per civilisation and code version (`sim/engine/economy_port_year.py`). Every seed starts from the same spun-up economy: the producers' opening capacities are identical across seeds. The seed only changes what happens afterwards (weather, events). Which production chains exist after the spin-up is itself a lottery, though: in Norse, whether a copper maker gets its plant built during the spin-up decides whether copper trades at all. Metal volatility is dominated by that draw. Changing one expectation constant from 0.5 to 0.55 moved Norse's six-seed median metal volatility from 0.69 to 0.20, and Rome's from 0.22 to 0.64.

So a six-seed median is one sample of the quantity that matters most, and a change can look like a large gain or loss by luck. Complaints/reports/agent-economy-review-round-three.md records one such case.

Evidence: compare the producers' `capacity_runs` at the first year across seeds (identical), and the sweep described in the round-three report.

What it would take: let the seed reach the spin-up (or run several spin-ups per civilisation) in the port and in `economy_validate.py`, and report medians over spin-up draws as well as seeds.

Related: 387.
