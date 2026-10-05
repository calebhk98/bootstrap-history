# Validation seeds share one spin-up, so a median over seeds is one draw

**Status:** closed - the spin-up draws nothing from the seed; sim/tests/test_spin_up_seed_free.py

`python3 sim/economy_validate.py --seeds 1,2,...` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`) plays each civilisation from the agent economy's hidden spin-up, which is cached per civilisation and code version (`sim/engine/economy_port_year.py`). Every seed starts from the same spun-up economy: the producers' opening capacities are identical across seeds. The seed only changes what happens afterwards (weather, events). Which production chains exist after the spin-up is itself a lottery, though: in Norse, whether a copper maker gets its plant built during the spin-up decides whether copper trades at all. Metal volatility is dominated by that draw. Changing one expectation constant from 0.5 to 0.55 moved Norse's six-seed median metal volatility from 0.69 to 0.20, and Rome's from 0.22 to 0.64.

So a six-seed median is one sample of the quantity that matters most, and a change can look like a large gain or loss by luck. Complaints/reports/agent-economy-review-round-three.md records one such case.

Evidence: compare the producers' `capacity_runs` at the first year across seeds (identical), and the sweep described in the round-three report.

What it would take: let the seed reach the spin-up (or run several spin-ups per civilisation) in the port and in `economy_validate.py`, and report medians over spin-up draws as well as seeds.

Related: 387.

## Resolution

The premise was wrong in one respect: the seed does not reach the spin-up because nothing in the spin-up is random. Measured by `python3 -m sim.tests --only spin_up_seed_free`: no module in `sim/economy/` imports a random source, and `opening_values` (the spin-up cache key's content) is identical for different game seeds. So there is no stochastic spin-up to key on the seed, and keying the cache on it would only duplicate the same record.

What remains true: a median over seeds samples what happens after the spin-up, from one fixed starting point, and which production chains the deterministic spin-up builds is sensitive to the inputs. Sampling that needs a perturbed opening (a different feature, not a seed), and it belongs with the validation tool when it returns.
