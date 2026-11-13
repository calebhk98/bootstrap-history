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

**New evidence: the spin-up is chaotic.** A change that alters only the last digit of about one in seventy input bills
(the summation order of `close_kernel.close_rows`; merge d77138668, measured by instrumenting every call in a Norse run)
moved Norse's inventory gap by a factor of three and its price gap by a factor of three; installing numba mid-session
also changed Norse's trajectory although `sim/jit.py` says its settings keep a game reproducible (not checked further).
So the yearly change over the last few years of one trajectory is largely where the chaos happens to land, and a rule
change can be judged only by its effect on many perturbed runs, not on one.

**Proposal (not built).** Judge settling as stationarity of a distribution, which CLAUDE.md 4.2 already asks of the
baseline: run the trimmed stage for a longer window, and require for each quantity (a) no trend: the change between the
mean of the window's first half and its second half under the tolerance, and (b) bounded fluctuation: the spread of the
year-to-year changes under a stated bound; and run a few spin-ups whose opening differs in the last digit (a seed of
rounding) to show the result does not depend on the draw. Keep the fixed-point test as a reported figure.

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

## 3. The opening's cash and savings once the own-plot floor is met first

**What was found.** The yearly household orders now meet the floors a household's own plot grew before sizing its budget
(merged on this branch). The opening (`opening_own.py`, `opening_demand_kernel.py`, `opening.py`) still applies the old
late cut, and it also gives households a "purse" equal to the money that late cut freed. Porting the yearly rule to the
opening (branch `opening-grown-floor-budget`, not merged) removes that purse. The households' savings then shrink, and
with them their store-of-value bids for silver and the ores, so on Norse the ore and silver markets stop trading at the
opening and the opening moves more in its spin-up, not less (`python3 sim/simulator.py opening-checks --civs norse_900ad`
on each branch). Measured in two steps: the rule alone breaks them; removing the purse code changes nothing further.

**Question.** What cash and saving should the opening give households? The old purse was a by-product of the leak, so
it has no economic reason behind it; but the opening's silver and ore demand rested on it. Options: (a) households open
with the cash balance they would hold at the stationary state of the yearly rule (their `cash_target` plus a year's
saving), derived from the same budget rule; (b) leave the opening as it is and accept that it disagrees with year one
(Complaints 545 and 607 stay open). The branch keeps (b) for now, since the spin-up only needs the yearly rule to be
consistent; the opening work is parked on its branch with this explanation.

## 4. Silver at parity, far above its making cost

**What was found.** Norse's money is weighed silver. Its design (`currency.has_mint` and `mint.py` docstrings) says the
metal is exchanged at parity, but the code paid sellers their ask, which fell with the price level; smelters then planned
on a thin margin and made far less than the coin wore away. The branch now pays parity (`mint_price.paid_in_metal`), and
Norse's money stock holds (`money_against_wear` passes). But silver now trades at parity, well above the bound of
`price_over_cost_coin_metal` over its making cost (`python3 sim/simulator.py opening-checks --civs norse_900ad`).

**Why it needs a decision.** For a money metal at a fixed price, a price far above making cost is what should draw more
mining until the best seams are taken and cost rises toward parity: that is the anchor of a commodity-money price
level, and it works over decades, not in the opening year. So the check may be asking the wrong thing of the coin
metal: the economically meaningful bound may be that silver's cost does not exceed parity (otherwise the mint gets
nothing) and that the gap is shrinking, not that the price sits near cost. Complaint 519 asks the same about silver and
gold.

**Question.** Should `price_over_cost_coin_metal` keep its band for a metal paid at parity, or test that parity covers
cost? The branch does not change the check.

## 5. The environment was missing numba

`requirements.txt` lists numba, and `sim/jit.py` runs the kernels as plain Python without it ("much slower"). This
session's cloud environment did not have it until an agent installed it mid-session; a Rome opening took about an hour
before and the five civilisations' opening checks took about half an hour together after. If the environment's setup
does not install `requirements.txt`, it should (`pip install -r requirements.txt`). `sim/jit.py` says its settings keep a
game reproducible with or without numba; that was not checked here.

## 6. A new trade's crew that never runs never learns (Mexica's tools)

**What was found** (Mexica at d77138668, scratch probes; no committed command prints a producer's practice by year).
On main, Mexica had no maize, millet or cacao producers at all: every recipe with an iron tool was uncostable, and its
staple and coin-metal checks read cost estimates of goods nobody made. On the branch those producers exist and run,
but by hand, because almost no wooden tools are made. A new wooden-tool crew starts unpractised and
`practice.recipe_for` (sim/economy/practice.py) multiplies its hours several-fold; at that cost its plan's
`share_working` is nil, so it never runs, so it never practises, so the penalty never clears. Entry does not break the
trap: it subtracts the trade's nominal idle capacity (`entry.gap_beyond_spare`, `entry_margin.gap_at_entry_price`)
and sizes newcomers to last year's tiny traded volume (`entry_sizing.sized_runs`), and newcomers join the same crew.

**Question.** How should an unpractised crew decide to work? Options: (a) it plans at its practised hours and pays the
unpractised ones while it learns (an investment in practice, as an apprentice's first year is); (b) an entrant crew
starts at the practice of the trade's pool in the population when peers exist elsewhere; (c) leave the learning rule
and fix only entry, so it counts capacity that can actually be staffed. `Complaints/reports/research-how-a-brand-new-trade-forms.md`
is the background. The branch makes no change here.

## Where it stands (branch spin-up-settles)

Merged, each with a rule test: the own-plot floors met before the budget is sized; unmet need read against the
economy's food need; the mint bids where its metal trades and weighed metal is paid at parity; a residue left by decay is
removed and is not an offer; an unpriced tool is costed by its fallback chain; and `spin-up-trace --stages`, a committed
command that prints both spin-up stages year by year with the settle gap of each quantity. Complaint 473's Update 24
has the mechanism and evidence for each, and the branches tried and not merged.

`python3 sim/simulator.py opening-checks --civs <civ>` on the head, against main's last rebuild (Complaint 970):
- Norse, England, Han, Rome: the price-over-cost checks pass for all four; Rome now passes money against wear (it
  failed on main); Han's coin metal now trades. Still failing: spin_up_settled for all four; money against wear just
  under its bound for Norse and Han; the wage over its floor for Rome.
- Mexica fails more checks than on main, but main's passes were cost estimates of goods nobody made (question 6). On
  the branch the money no longer drains (money against wear passes); food stays dear because the crops run by hand
  while the tool makers' crew is caught in the learning trap.

So 473 is not closed. What I would do next, in order: decide question 1 and build the stationarity test on the ensemble
(`spin-up-trace --stages --ensemble N` exists), since single runs cannot judge a rule; question 6; the
measure of the rate (Norse's whole gap is one year's step of a rate that is otherwise flat, question 1); then the
remaining movers that `spin-up-trace --stages` names for each civilisation.
