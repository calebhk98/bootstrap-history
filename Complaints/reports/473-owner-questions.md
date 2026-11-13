# Complaint 473: questions for the owner (branch spin-up-settles)

Written while working on 473 alone. Each question says what was found, why it needs a decision, and what the work
does in the meantime, so it can be answered without the session's context. Nothing here blocks the work: each
question has a default that the branch follows until answered.

## 1. What "settled" should mean for the spin-up

**What the check asks now.** `spin_up_settled` (sim/markets/spin_up_run.py `final_result`, sim/markets/spin_up_gap.py)
passes only if, over the last `SPIN_UP_MEASURED_YEARS` hidden years, every one of these moves less than `SPIN_UP_TOLERANCE` from one year to the next: the basket
price level, the interest rate (against `SPIN_UP_RATE_FLOOR`), real output, hired hours, producers' inventory value, unmet
food need (against `SPIN_UP_UNMET_FLOOR`), and each of the `SPIN_UP_WATCHED_GOODS` goods the opening basket spends most on.

**Why it matters.** That is a fixed point, not a steady state with noise. Among the watched goods are thin ones
(Norse `steel_noric_kg` falls to a small fraction of its opening price and moves by large shares a year; a per-year
probe of the spin-up shows it, and no committed command prints per-good prices by spin-up year). A deterministic
economy can in principle reach a fixed point, but an agent economy with lumpy producers usually settles into small
cycles in thin goods. CLAUDE.md 4.2 asks the baseline to be "a plausible draw", which reads more like a stationary
distribution than a fixed point.

**Question.** Should the check stay a fixed point (every watched quantity under the tolerance), or should it test
stationarity (no trend over the window, and fluctuation within a bound) for the thin goods? The complaint says "do
not weaken the settling tests", so the branch keeps the check as it is and tries to meet it. If the economy ends up
trendless but a few thin goods still cycle, I will report that and not change the check without your answer.

## 2. People on tiles with no farmland

**What was found.** In Norse, tiles with fertility exactly 0 (norway_02, norway_03, sweden_04, sweden_05, finland_03 and
the three Svalbard tiles) hold a sizeable minority of the people and most of the unmet food need (measured with a scratch probe of the
spin-up; no committed command splits hunger by tile fertility). They get no plot
hours at all (`household_hours_year.usable_plot_hours` returns 0 for fertility 0), their market areas sell out of food,
and their wages cover a small share of the food floor's cost. Raw millet meanwhile sits unsold in the fertile
sweden_01 area while bread, flour and cooked meal go unmet there.

**Question.** Is fertility 0 on those tiles intended (high fell, tundra, ice), with their people meant to live on
fishing, herding and trade? If so, the gap is that nothing carries food to them and nothing produces their food
locally; if not, it is a data question for the geography. The branch does not change the data; it fixes the money
leak first (below) and re-measures.

## Findings so far (for context)

- The drift in every civilisation is a contraction of the money flow, not of the money stock: coin moves from
  producers to households, households' spending tracks their income, and income falls as producers shrink.
- The main leak found: a household's budget is sized as if it bought its whole food floor, and only afterwards are the
  floors its own plot grew removed from its bids. The money this frees is neither spent nor offered to lenders
  (sim/economy/households_orders_kernel.py, the cut "the floors the own plot grew are not bought"). Being fixed.
- The interest rate jumps because the declared partial adjustment toward the clearing rate is overridden by three
  snaps in nearly every year (sim/loans/clearing_kernel.py `settled_rate`). Being fixed.
