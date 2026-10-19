# The opening's income is a fixed point that leaks saving, and fixtures state an income to avoid it

**Status:** open

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

Depends on 605, 606, 538 and 545 (545 cannot land alone). The unmerged rate search is on branch `fix-526-opening-rate` (`sim/economy/opening_rate.py`) and may be revived here.

**What is wrong.** The opening sets household income as the fixed point of income and the demand it pays for. Households save part of any surplus and nothing spends it (no producer plant, working capital or lending demand), so the fixed point falls to the households' floors. Fixtures state an income through `EconomySetup.opening_income_per_head` to get a surplus.

**Evidence.** `sim/economy/opening_income.py`; `python3 sim/simulator.py opening-checks`; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

**Why it matters.** A society's surplus follows from its productivity, not a stated income (CLAUDE.md 4.1, 4.2).

**What it would take.** Opening income is the value of what its workers produce at opening prices, with saving matched by investment (producers' plant and working capital, and lending). Delete `opening_income_per_head` and the fixtures' use of it. Regenerate `openings/` with `python3 sim/simulator.py openings`, or ship with `--allow-failing REASON`.

**Test.** Realised year-0 income is within a band of the opening figure; a more productive technique set opens with a larger surplus; the spin-up settles (which also needs 608 and 473); `grep -rn opening_income_per_head sim` is empty.
