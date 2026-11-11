# Rome slides after year seven through a producer contraction loop fed by unspent household budgets

**Status:** open - diagnosed on branch claude/labor-market-economy-stability-ueffy1; the rationed-budget part was to be fixed on that branch, but this diagnosis predates the A1/A2 fixes of Complaint 964

**Re-measure:** diagnosed before the A1/A2 fixes of Complaint 964; the figures here are from an earlier build and need re-measuring.

**What is wrong.** On a saved Rome economy stepped on the branch code, real output falls about seven per cent a year from
year seven, and the unsold-hours share and the people-based rate climb with it. Measured from a copy saved at year seven
(probes in the session scratchpad `ld/`; no committed command breaks the fall down):

- Hours wanted by employers fall about two fifths in five years. About three tenths of the fall is the state's labour
  bids as its treasury runs down to its reserve, about a quarter is stone-block producers sized at the opening for sales
  ten times what they sell (a transient), and the rest is a broad fall of several per cent a year.
- Households fill only about a third of the money they bid: most of the rest sits in markets that offer a few units
  against bids hundreds of times larger (bronze, brass, olive oil, meat, leather, cheese, land). The unspent money is
  saved, so households' cash rises while producers' falls, and the demand it was meant for never reaches anyone.
- Producers plan below their expected sales (to work off stock and on thin margins), sales follow plans, expected sales
  follow sales, and incomes fall with hours. In ablations, keeping expected sales from falling and removing the stock
  working-off together stop the slide; either alone halves it; `share_working`, unmet-demand visibility and household
  budgets alone change almost nothing.
- Scarce, rationed markets do not draw more supply: asks raised to turned-away buyers stop at the cost band, and
  capacity grows at most a quarter a year (and only for recipes without plant through the capacity-growth rule).

**What it would take.** Rationed budget spent within the year on the need's substitutes and then other needs (Eurace's
second choice); scarce markets that draw supply (capacity and entry that respond to standing rationed bids for goods with
plant too); the opening's sizing of stone-block and similar producers to what sells (Complaint 961).

**Measure.** `rome_step.py`-style stepping of a saved opened Rome economy, or `python3 sim/simulator.py spin-up-trace --civ rome_100ad`.

**The ask floor is not the limit.** With households respending rationed budget, output holds but the people-based rate
in wage trades still rises over a decade. An ablation on a saved Rome opening setting the ask floor
(`labour_ask_floor.py`) to half or to zero lowers the wage and the price level but changes employment by a couple of
points: even at a zero wage employers bid for little more, and by year ten nearly all idle hours sit in (trade, area)
markets with no extra bid at any wage. The limit is demand for labour, and people staying attached for years to trades
in their area that hire nobody (farmer, labourer, miner hold most idle hours). Side finding: in a few thin areas the
unskilled wage reads several times the national one, and it became every skilled trade's reservation there
(`unskilled_option`). Fixed in code by Complaint 965 (the option counts only for the hours the unskilled jobs can take,
`sim/labour/market/unskilled_reach.py`); awaiting 965's game measurement.

**Idle workers reconsider their trade at the share that found no work** (merged): raised Rome's real output in the middle
years. Two further changes are parked: idle workers leaving a dead trade for their plot (lowered output), and
`Complaints/reports/962-intake-and-cross-trade-migration.patch.txt` (a trade learned within a season takes people up to
its unfilled vacancies; idle workers weigh other areas' trades they can enter; migration decides in rounds): refused
switch requests fall from about three quarters to under half and the people rate drops a couple of points, but real
output ends about a tenth lower and the cause is untraced. Training intake rests on `APPRENTICES_PER_MASTER` and training
years with no opened source for most trades.
