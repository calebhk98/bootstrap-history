# The opening's income is a fixed point that leaks saving, and fixtures state an income to avoid it

**Status:** open - `opening_stationary.py` solves the stationary runs, hours and incomes but is not yet what the opening seeds from (473 Update 6); households count their firms' equity (605, closed), which lifts spending and lending a little; the leak is not closed

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

Depends on 606, 538 and 545 (545 cannot land alone; 605 is closed). The unmerged rate search is on branch `fix-526-opening-rate` (`sim/economy/opening_rate.py`) and may be revived here.

**What is wrong.** The opening sets household income as the fixed point of income and the demand it pays for. Households save part of any surplus and nothing spends it (no producer plant, working capital or lending demand), so the fixed point falls to the households' floors. Fixtures state an income through `EconomySetup.opening_income_per_head` to get a surplus.

**Evidence.** `sim/economy/opening_income.py`; `python3 sim/simulator.py opening-checks`; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

**Why it matters.** A society's surplus follows from its productivity, not a stated income (CLAUDE.md 4.1, 4.2).

**What it would take.** Opening income is the value of what its workers produce at opening prices, with saving matched by investment (producers' plant and working capital, and lending). Delete `opening_income_per_head` and the fixtures' use of it. Regenerate `openings/` with `python3 sim/simulator.py openings`, or ship with `--allow-failing REASON`.

**Test.** Realised year-0 income is within a band of the opening figure; a more productive technique set opens with a larger surplus; the spin-up settles (which also needs 608 and 473); `grep -rn opening_income_per_head sim` is empty.

## Evaluated and built (branch `605-607-saving-finds-a-use` (merged as `44cd2125`, then deleted; `equity.py` is in main, `opening_equity.py` is no longer in `sim/economy`))

Three ways to give saving a use were weighed against the code:

1. Households buy producers' equity or plant. The code already has the channel: a new workshop is staked from its
   owner's cash (`open_entrants`), a plant is built from a loan the funds market makes (`_lend`, `expansion` and
   `enter` requests), and dividends return the profit. What it lacks is the household side of the ledger: the
   firms the household owns were not part of the wealth it wants, so it also tried to hold that wealth as cash
   and saved what nothing spent. Built (605): `view.equity`, counted in `goods_orders`.
2. The funds market lending to producers' expansion. It exists, but the fixture has no plant at all (every recipe's
   `plant_life_years` is zero), so no producer can ask for an expansion loan: saving there has literally no user.
   The tests use `plant_setup()` (plant on the farm and the mine). Working-capital and entrant requests are the
   only other demand for funds and they are small against the stock on offer.
3. The opening holding households at the wealth they want. The opening's firms are worth little against a wish
   of years of surplus income (an `opening_equity.py` counted them in the settlement; it is no longer in `sim/economy`); the settled income over the
   ceiling moves by about a hundredth of itself. The wealth the wish asks for does not exist in the opening, so
   only a smaller wish (606) or assets that do (538, land) can meet it.

Measured, fixture with plant, 40 quiet years, years 5 on (`python3 -m sim.tests --slow --only saving_finds_a_use`
holds the bounds; the figures below came from a throwaway probe that is not kept):

- household spending over income: 0.885 before, 0.92 after;
- the share of the savings on offer that was lent to a producer: 0.04 before, 0.10 after;
- mean hired share of offered hours: 0.43 before, 0.47 after.

Rome, first ten years of the hidden spin-up (throwaway probe, not kept; hired share of offered hours by year):
before 0.16, 0.08, 0.03, 0.03, 0.05, 0.075, 0.076, 0.082, 0.080, 0.077; after 0.25, 0.12, 0.10, 0.09, 0.09, 0.095,
0.085, 0.086, 0.094, 0.090. The labourer wage in year nine is 0.068 before and 0.111 after (opening 1.0 on the
earlier probe's scale); the fall is still about a sixth a year, so the collapse is slowed, not removed. Spending
over income in years two to nine rises from about 0.75 to about 0.9.

Small fixture without plant (`controlled_run(120)`): the settling statistics are unchanged except that the money
stock now settles; the hired share by decade is unchanged to within noise, since there is nothing to invest in.
`baseline_fixture: stocks are not eaten through` moved from passing to failing (grain 0.59 against a bound of
0.5): the grain stock alternates between zero and about a hundredth of a year's output every year (a two-year
cycle that exists before the change), and the check compares the first and last years of the window, which sit in
opposite phases. Not loosened; the cycle is 553/473.

What remains for 607: deleting `opening_income_per_head` needs the opening to hold the wealth its households want
(606's wish shrunk to sourced figures, 538's land) so the fixed point is not at the floors, and a fixture with
plant as the default so saving has a user.

**Direction (2026-10-20).** With 606's sourced wealth figures, the opening's households should hold their wealth
mostly as land titles; the leak closes by giving saving that asset (538, 551) before any change to the wish.

## Update: not deleted

`opening_income_per_head` is still used by the engine's opening and by `surplus_game_openings`; deleting it waits for the
opening to seed its wage and runs from `opening_stationary` (473 Update 7). The stationary fixture states no income.
