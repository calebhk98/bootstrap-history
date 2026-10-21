# Complaint 473 history: measured sections moved out of the complaint

Each section is verbatim from the complaint as of the move, in its original order. Branches marked deleted were not merged; re-measure before relying on a figure. `Complaints/473-*.md` carries the current state and an index of these sections.

## Update (coin wear and the spin-up report)

Done:

- **A measurement exists.** `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60` prints the price
  level, money stock, rate, coin worn, coin struck net and metal at the mint by year (`sim/engine/economy_port_trace.py`,
  `economy_api.money_year_figures`, from each year's `YearOutcome.money_audit`). It runs the first stage on the
  opening the game saved, without stopping at the tolerance. `sim/tests/test_spin_up_money_supply.py` (slow) reads
  the same trace.
- **The spin-up now says whether it settled.** The first stage returns `{settled, years, gap}`; it is saved in the
  record (`EconomyRecord.spin_up_result`), read through `game.economy.spin_up_result()`, and `simulator.py openings`
  prints "NOT SETTLED" for an opening that ran out of years with the cycle still moving.
- **The drain is measured, and it is the wear sink with nothing replacing it.** Rome, 60 years (command above, the
  harness game): the money stock goes 45.5 to 25.2 billion units (a fall of 45 per cent, still falling), decade means 43.4,
  39.0, 35.5, 31.9, 28.6, 26.4; the mint's strikes over each decade are between minus 12 and plus 21 per cent of the
  coin worn. The audit identity holds (stock change equals struck less worn, other edges about one per cent of wear), so
  wear is the only steady sink and the mint is not a steady source.

Cause, found by tracing the silver market and the chain behind it (not the mint's rule):

1. The mint quotes both ways at one price (Rome's coin standard has no mint charge), so the coin metal's price is
   pinned at the minted value and the mint buys every kilogram offered. Nothing in the mint's decision starves it. The
   price of the metal in goods still follows coin scarcity through the price level; what fails is the supply that
   should answer.
2. Metal reaches the mint only from the producers of silver and from households selling bullion. Households' flows
   are large both ways (hundreds of thousands of units a year bought from and sold to the mint, net melt about an eighth
   of wear) and cancel. Producers supply almost nothing after the first two years: the opening's silver comes from
   lead smelting (a joint product, 1.6 kg a tonne), about 15 per cent of the year's wear in year zero and next to nothing by year three.
3. Lead smelting stops because its galena is never bought. The opening sizes lead capacity to the silver demand
   households' store-of-wealth bids put into final demand (about a year of wear), but the galena deposits' declared
   capacity can feed only about a quarter of that, and the smelters are placed by population, not beside the galena
   (`opening._place_producers` places a sited input's users first). From year three smelters bid in tiles with no
   galena offered, and mines in tiles with no smelter hold unsold stock (seven hundred million kilograms offered, none
   traded, each market area being one tile). Galena, then lead, then the by-product silver stop.
4. The dedicated silver chain (ore, jarosite, smelting) is a newcomer chain: entry builds the smelters (hundreds of runs
   of capacity) before any ore is mined and at tiles with no ore, so by year twenty the smelters work a few runs of their
   capacity and the ore mines about a seventh of theirs.

Tried and not merged (each measured on the same 60-year trace, same opening): leaving the mint's standing bid out of the
volume the remembered price is weighed against (`market_memory_asks.wanted_at`); charging a newcomer's tile for carrying
its inputs from the nearest tile that makes them (`location.entry_siting`); placing processors beside where their
heaviest input is made at the opening (`opening._place_producers`, sited recipes first). None moved the stock or the
mint's strikes by more than a few per cent over 60 years; the first only matters if the metal's price memory is frozen,
which it is not on the real opening. They are described here so the next attempt does not repeat them.

What remains (in `test_spin_up_money_supply.test_the_money_stock_keeps_up_with_wear`, which fails on purpose: after
forty years the stock is 0.74 of its first decade's, against the 0.90 that one decade of unreplaced wear leaves):

- The silver chain has to be supplied from the opening: capacity that agrees with the deposits' limits (not a year of store
  building), processors beside their sited inputs, and a smelter chain that does not outbuild its ore. That is the
  opening's capacity/income mismatch above and waits on the owner decision in 507.
- Do not weaken the test. Regenerate `openings/` (`simulator.py openings`) when this lands; the shipped entries are keyed
  on the source and every source change leaves them unread.

## Update 2 (material orientation; why the chain still cannot feed the mint)

Answers to the three questions, each measured on the Rome opening (`harness.sim()`; no committed command prints these,
they were read from the opening record and from each year's `YearOutcome.output` of an `Economy` stepped as
`economy_port_trace.spin_up_trace` does):

1. **Why ore did not reach a smelter in another area.** Nothing is broken in the merchants: they carry any good whose price
   gap beats carriage, interest, spoilage and margin. The galena smelters were 104 tiles wide, 6 per cent of their capacity
   on a galena tile and the rest a mean of thousands of money units a tonne from the nearest ore (the carriage of a tonne of
   ore across the map is many times its value, so no gap can pay for it; the nearest pairs of tiles were marginal).
   Galena's market areas are about a tile each. So the fault was siting, not trade: `opening._place_producers` put a
   processor where its output is demanded and `location.entry_siting` priced only the carriage of the output.
2. **Why entry built more than its input supply.** `entry_sizing.sized_runs` already holds a newcomer to the traded volume of
   its inputs, but read it at the tile where the output is wanted, then `location.entry_siting` moved the newcomer to another
   tile. It now reads the inputs at the tile where it is built (`works_at`).
3. **Why the opening sized lead to silver demand.** Households' store-of-wealth demand for the coin metal is about one year
   of wear, lead has no final demand, and the lead recipe makes silver as a by-product, so lead capacity is whatever makes
   that silver. That sizing is the 507 question; it is left as it was.

Built (general, no content ids): `sim/economy/location_inputs.py`. A processor whose input comes from a site-bound recipe with
declared limits (the opening's `incumbents` name it) is placed only in market areas of that input that hold supply, on the
tiles where the carriage of the run's inputs in plus its output out is least (each by the recipe's own masses, so a
weight-losing run settles at its inputs and a weight-gaining one at its market), within each tile's spare hands; what the
supply cannot feed is still built in proportion, so the shortage shows as the input's price (a cap at the supply removed the
scarcity premium that `mine_supply_enters_clearing` asserts). Sited recipes are placed first in `_placement_order`.
`location.entry_siting` adds the same input carriage for fixed-site inputs and considers the tiles holding them. Result at
the opening: lead smelting on a galena tile went from 6 to 71 per cent of its capacity and the mean carriage from the nearest
ore from thousands to single digits a tonne; the processors of countries with no ore in reach are no longer built.

The earlier "input carriage in siting" try changed entry only, so the opening placement (smelters by demand, ore out of reach)
still held; and a smelter placed beside ore alone does not help either, as below.

**The finding that stops the test.** With the chain sited beside the ore the first year makes more silver (about 1.6 times the
old figure) and the mint still strikes about nothing over the run: `last/first` of the money stock over 60 years is about 0.59
(the earlier 40-year figure was 0.74, the new one 0.73; not a gain). The reasons, in order:

- The declared deposits cap the silver the economy can ever make at roughly 0.3 of the first year's wear (galena capacity over
  the ore a run takes, times the silver a run makes, plus the silver-only deposits; `SiteLimit`s of `galena_kg` and
  `silver_ore_kg`). Wear is 1 per cent of a stock the opening derived from households' balances at the opening wage, which
  falls several-fold in the first year (the 507 mismatch). Even a perfect chain therefore settles the stock near 0.3 of its
  start: no supply-chain change can make `test_the_money_stock_keeps_up_with_wear` pass; that needs the opening stock and the
  deposits to agree (507) or the data to change.
- Within that cap the chain still dies in three years, now beside its ore: the lead each smelting run makes has no buyer
  (no final demand), the unsold lead trips `producers.runs_for_stock`, which gates a joint recipe on its main output by
  quantity (`producers.main_output`), and the silver that sells to the mint at its minted value stops with it. A joint recipe
  whose by-product pays should be gated on the value of what is left unsold, not on the heaviest output. Not changed here;
  worth a regression test of its own, and worth ~0.3 of wear at most.
- `economy_no_offer_memory`'s final-year price check sits at its threshold on the old code (0.00402 against 0.004, swinging
  between 0.00398 and 0.00456 in the preceding years) and flips with any change to siting; the haul term is restricted to
  fixed-site inputs so that fixture is untouched.

Not done: opening capacity/income sizing (507), the joint-recipe stock gate, regenerating `openings/`.

## Update 3 (joint recipes gated on value)

`producers.runs_for_stock` judged a joint recipe on the stock of its heaviest output (`main_output`), so unsold lead stopped
a smelter whose silver sold. It now takes the run's cost and the outputs' prices (`plan` passes them): an output that is
piling up is ignored while what a run makes of the others, at those prices, covers the run's cost; otherwise the largest
pile limits the runs as before (a single-output recipe is unchanged). Readers: `producers.plan` (the one caller that passes
the cost), `test_economy_producer_stale_ask` (no cost, old behaviour). `main_output` is untouched; its other readers are
`year_close` (output worked, a producer's own figures) and the opening's placement.

Effect on the Rome trace (`simulator.py spin-up-trace --civ rome_100ad --years 40`): the mint's strikes over wear by decade went
from about nil to 0.17, 0.22, 0.34 after the first decade, and the stock ratio last/first from 0.73 to 0.78. The test still
fails: the first years are not rescued, because the smelters' own bids push the ore price up until the silver alone does not
cover a run (the chain is sized to silver demand, 507), and the deposits' ceiling above still applies.

## Update 4 (stage 2 of 507: the opening seeded from costs)

Built on `507-stage-2-opening-from-costs` (ONE_PRICE_OWNER_PLAN.md, Stage 2 "Done"): household income settled with the demand it pays for,
plant sized to the share that works, workforce placed for the runs producers expect to sell, producers opening with their
inputs, recipes ranked with deposit ceilings and demand-limited co-products, the metal the money loses a year as the mint's
final demand, and the coin priced at the marginal cost of its metal.

Fixed: the money stock follows from the transactions and the metal's cost, the chain behind the coin metal exists at the
opening, and `test_the_money_stock_keeps_up_with_wear` passes unchanged (the mint's strikes are about wear over the
last decades; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`).

Not fixed (so this complaint stays open): the spin-up still reports not settled for every civilisation. The price level no
longer cycles but falls for decades with the wage, while employment grows into the gap; realised income in the first year
is a small share of the opening figure. The cause is the wage: the labour market clears at the households' outside option
from the first year, and prices follow it down slowly. Seeding the wage at that level does not help because prices and the
outside option scale together. What it needs is a settled model of how a labour glut passes into prices (the economy's rent
and price search, stages 5 and 7), then a spin-up that runs until its tolerance is met.

## Note (2026-10-15)

`MONEY_LAG_YEARS` for England in `sim/tests/money_regimes_play.py` moved from three years to four in merge
fix-round-regressions-3, because after the ore districts merge (520) extra metal overtakes the base series a year
later while both series' price levels climb steeply. That loosens the check; restore it when the opening's money stock
is fixed (507 Stage 2) and the price level stops climbing. Stage 2 (Update 4) moved it to five years: the price level still climbs.


## Measured: the settling statistic on Rome, main against the in-year price search (507 Stage 7)

`sim/economy/settling.py` over 60 years of the Rome first stage (`economy_port_trace.spin_up_trace(harness.sim(), 60)`,
then `settling_report(rows)`; `python3 -m sim.tests --slow --only baseline_rome` runs the same check). On the integration
branch before Stage 7 every series fails: the price level swings by up to half a log unit a year around a level that
wanders over several times, the market rate reaches the ceiling `bounded_rate` sets, and the wage and the money stock
trend down. With Stage 7 (branch `507-stage-7-price-search-within-year` (deleted unmerged; its code is lost)) the rate's yearly steps and the price level's
swings shrink to a fraction of that and the money stock settles; the price level and the wage still fall steadily,
which is the labour glut (608), not a cycle. Reproduce both with the command above on each branch (minutes each).

## Measured: what made the integration branch's spin-up swing (fix-settling-regression-exit-and-trim)

Probe: the Rome first stage, 21 years (`economy_port_trace.spin_up_trace(harness.sim(), 21)`): largest price level
over years 5 to 20, largest and smallest market rate, wage at year 20. The trace builds a blank economy from the
opening, so only data and the opening's workforce reach it; the post-spin-up trims (`workforce_settle`) and the
`expected_hours` rule cannot.

| head | max price level | max rate | min rate | wage 20 |
|---|---|---|---|---|
| pm-merge-staging before 556b | 2.610 | 0.276 | 0.063 | 0.107 |
| plus 556b merged | 3.641 | 0.370 | 0.100 | 0.217 |
| no second trim | 3.641 | 0.370 | 0.100 | 0.217 |
| 467 data reverted (farmer training 1, no fallback flag, slaves and bonded as labourers) | 0.904 | 0.171 | 0.023 | 0.309 |
| farmer training 0 and fallback flag only | 3.641 | 0.370 | 0.100 | 0.217 |
| farmer training 1 with the fallback flag kept (final) | 0.904 | 0.171 | 0.023 | 0.309 |

The swing comes from the farmer trade's training years being 0 (with the exit valuation of the earlier finding
in place, so that change was not the cause on this head). The second trim, the `expected_hours` rule and the strata
trades do not move the first stage. Farmer keeps its one year of training; the labourer's `fallback` flag stays so the
two do not tie.

The 467 check's purpose (no trade opens holding several times its jobs) now excludes the plot trade, whose people
work their own land and wait on no bid, and trades with under one worker-year of jobs (glassblower holds about a
millionth of a person against a few thousandths of an hour, a ratio of noise).

## Measured: which merge tips the spin-up into cycling, and what the cycle is (branch 473-why-the-spin-up-tips-into-cycling)

Probe as in the table above (Rome first stage, 21 years: max price level over years 5-20, max rate, min rate, wage 20), each
first-parent merge with the farmer-training fix (the data and `strata_seed` part of merge 2d40eaa4's second parent) applied on top.

| commit | max price level | max rate | min rate | wage 20 |
|---|---|---|---|---|
| 49896150 (556b) + fix | 0.904 | 0.171 | 0.023 | 0.309 |
| d9551124 (621-623) + fix | 4.973 | 0.394 | 0.108 | 0.198 |
| 73655a13 (619b recipes book their trades) + fix | 4.048 | 0.301 | 0.112 | 0.214 |
| 2d40eaa4 (head) | 2.491 | 0.316 | - | - |
| head + price level chained over what households bought (tried, not kept) | 1.380 | 0.184 | 0.053 | 0.105 |
| 49896150 + fix + the same chained level | 1.222 | 0.258 | 0.033 | 0.608 |

The tipping merge is 619b: a pure data rebook (brick, ceramic, wick and tar hours from the generic labourer to potter, spinner,
charcoal burner). 537, 619c and 600 were not probed (619b already cycles).

What the cycle is (per-year traces of the 619b and 556b configurations; the scripts were scratch, no committed command prints them):

- Both configurations share one slump: producers' runs fall to under a tenth of capacity in year 2, the hired share of offered hours is
  3 to 8 per cent throughout, the wage falls to a third, capacity halves in years 5-6. That is the labour glut (608), not the cycle.
- The "price level" is a fixed basket of the opening's wanted quantities over goods that traded recently. At 619b the opening gives piped
  water, iron bar and raw glass a few thousand runs of capacity; at 556b it gives them none, so they never trade and sit out of the index.
  Once they trade, their basket quantities (piped water 781e9 kg against 23e9 made; iron bar 52e6 against 1e6 made, none bought by
  households; glass 152e6 against 3e7) are far above supply, their prices climb two orders of magnitude (water x380, glass x400, iron x130
  by year 13) and they carry most of the index while stone, brick and millet stay at or below base. Households' actual spending on piped
  water is 5 to 9 per cent. Expected inflation, the savers' ask (the rate floor), cash targets and the state's real spending target read this
  index, so the rate sits at 0.1 to 0.3 (against 0.03 to 0.17) and lending is several times larger.
- Supply does not answer a 100-fold price: water capacity stays near 1.95e3 runs for fourteen years (loans for about a tenth of capacity are
  funded each year, little plant arrives); glass plant lasts 3 years so expansion only replaces wear; the bloomery runs 0.1 to 5 per cent of capacity.
- The opening decides by a threshold which thin goods have any capacity at all. That is the sensitivity: a few recipes' labour rebook moved
  those goods across it, as farmer training years did earlier.

Tried: a Tornqvist chained index weighted by households' spending shares. It lowers the head's swing (2.491 to 1.380; rate 0.316 to 0.184)
but moves the calm configuration the other way (0.904 to 1.222; rate 0.171 to 0.258), so it does not make both calm and was not kept.
The index is part of the loop, not all of it.

Not tried: planning to the area's demand in single-area thin markets (the baker/flour overshoot reported by the coordinator). The traces show
the opposite direction for the thin goods that dominate the index (runs far below capacity at high prices), so it is probably another mechanism; unmeasured.

## The opening basket held to supply (merge 66da3cd3)

The spin-up's tipping came from the opening household basket: it was the households' full final demand, never held
to what the opening's producers could leave for them, so a thin good the opening supplied little of (bronze, brass,
iron bar, piped water, silver, glass) entered the price level index with a wanted quantity many times its supply, and
its price, rising by orders of magnitude, carried the index, expected inflation, the savers' ask and the state's real
targets. `sim/economy/opening_basket.py` now holds each good's basket quantity to the supplied part (the raw demand is
kept as `opening_demand` for the coin metal's marginal cost). Probe (`settle_probe.sh`: Rome, years 5 to 20) before and
after on the same head: maximum price level and rate fall from cycling to calm, and the old destabiliser (the farm
trade at no training years) no longer tips it. The labour glut remains: the wage still falls through the spin-up (608).
Measure with the probe or `python3 -m sim.tests --slow --only baseline_rome`.

## Measured: where the unhired hours are (branch 473-why-so-few-hours-are-hired)

Rome first stage, years 0 to 11 (`economy_port_trace.spin_up_trace(harness.sim(), 12)` with the economy's `clear_labour`,
`own_production` and `producers.plan` wrapped to add up hours; the wrappers were scratch, no committed command prints
the split). Shares of the hours households offer (working people times the year's hours; the withheld share is nil, so
all of it reaches the market):

- Own-plot growing takes about a tenth (food floor at about two-tenths of an hour per unit; a cohort's floors need under
  a twentieth of its hours). `households_own` caps it at the floors, so it is not idle and is not counted as hired.
- Employers hire about 5 per cent after year 2 (about 18 per cent in year 0). Their bids are close to what is hired
  (vacant hours under 5 per cent of hired), so there is no shortage at the cleared wage: the glut is on the demand side.
- About 85 per cent of hours are offered, unhired and not needed by any floor. That is not an artefact of booking
  (case a): own-plot work is already outside the market figures. But those hours are not idle in life: the model has no
  household production beyond the floors' land-only goods (spinning, building, fuel, tools, cooking), so self-employed
  time beyond the floors shows as unemployment.
- Why producers hire so little (case c, plan side): of the hours the plant could work, in years 1 to 11 the limit that
  binds is the stock gate (`producers.runs_for_stock`) for about three quarters of the lost hours, the yearly change
  limit for most of the rest, land caps next; unprofitable runs and cash are each a few per cent. Producers sit on stock many
  times their expected sales (year 6: millet stock about thirty times its expected sales; stone blocks, clay, firewood,
  meat likewise), so the market for what they make is small, not their purse.
- Why the market is small (case b): households grow their food floors on their own plots in year one and cut their floor
  bids by it (`year_goods._less_what_it_grew`), while the opening sized millet, flour and the rest for households that buy
  those floors (545). Capacity and opening stock are therefore many times the first year's sales.

Tried and not kept: reading the opening's bids with the same cut (own-plot growing taken out of the floors producers are sized
for, a small module beside `opening.py`, with a value test on the fixture). The test passed, but the Rome probe went from calm
to a price level of about 650 (rate stuck at the ceiling): with flour not sized, its joint by-product bran has no maker while
households still bid for it, and its price (times 10^12 by year 8) carries the price-level index. So the sizing fix needs the
index and the joint by-products handled first (the same thin-good fragility as above); it is not a labour mechanism.
The head's probe is unchanged by this branch.

## Measured and not merged: expansion that replaces wear before it grows (branch `expansion-replaces-wear-then-grows` (deleted unmerged; its code is lost))

Building each year's wear back before growing by the expansion share lets short-lived plant goods (lead) grow, and the
20-year probe stays calm, but the 60-year trace surges earlier and higher than the head (price level about twice the
head's by year 30, the rate at its ceiling after): more plant bought each year pulls more money and thin inputs into
plant at once. The late surge on the head (years 30 to 43) is led by bricks and carts. Durables carry no age (wear
removes a share of the holding each year, `inventory.wear_moves`), so there is no replacement wave: household brick
bids stay steady while brick output falls far below wear within the first decade and nearly stops later, and cart
output stops within the first years while replacement bids stand with no seller at any price. See the idle makers
and no-seller price work. Reproduce with a 60-year `spin_up_trace` on each commit (about 10 minutes).

## Measured: why makers with plant sit idle while their price climbs (branch fix-idle-makers-at-high-prices)

Rome first stage, years 0 to 8 (`economy_port_trace.spin_up_trace(harness.sim(), 9)` with `producers.plan` and
`producers.produce` wrapped to print each limit and each input and hour actually held; the wrappers were scratch, no committed
command prints them). Across all cart, stone wall and bar-iron makers:

- In `plan` the price is not the limit: `share_working` is near the whole capacity for carts after year 2, cash and land do not
  bind. What binds is the yearly change from last year's runs (`within_a_years_change`) because `last_runs` is the runs
  achieved, which are nil or tiny, so each year plans a quarter of capacity; the stock gate binds for walls and carts in years 2-3.
- The plan's quarter is not what is run: carts plan and hire hours for it and achieve nothing (hours held in full, iron bar
  held nil). Bar-iron makers (the bloomery recipe) are short of bloom and charcoal; walls of mortar and blocks. The input
  bid ceilings sit at the live price plus the margin share, far below what the bar market clears at in years 2-5 (households
  and other buyers with ceilings many times higher take the little there is), while the price memory the plan reads rose
  slowly (the trade is a sliver of what buyers wanted at the old price, `market_memory_asks.memory_reference_volume`).
- Bloom, the bloomery's input, has no maker in the Chinese market areas at all, and bloom makers elsewhere shrink as their
  price stays under their cost. Experiment (not kept): weighing a trade against the usual volume alone left the cart and bloomery
  runs at nil; the chain is short, not only mispriced.
- A plan-side fix that lets a wide margin ramp faster would not move these runs (expected margins read from the memory price are
  narrow), and would loosen the limit that stops chains from amplifying; not made. The plan's behaviour at a wide margin is pinned
  by `sim/tests/test_economy_producer_wide_margin_plan.py`.

Where the fix lies: entry of an input maker where buyers exist and no maker does (bloom in a market area with only ore far away),
merchants carrying bloom and bar between areas, and the price memory under scarce supply. Not producers.py.

## Measured: entry does fire for a bloom market with no maker; it is built where the ore is (branch entry-where-buyers-have-no-maker)

Rome opening, first four spin-up years, `entry_trial.trial_entry_plans` wrapped to print each Chinese bloom market (scratch, no
committed command): every Chinese market area has bids and no maker, its recipe costs under the bids' ceilings, and a trial plan
is made each year in most of them (`entry_trial.demand_at` over the bids, a trial share of it). Nothing is missing from the
entry rule: with the small fixture, bids under the recipe's entry price draw no maker and bids over it draw one sized by their
quantity (`sim/tests/test_economy_entry_trial.py`, `UnmetBidsDrawAMakerTests`).

What happens to the plan: `location.entry_siting` considers the area's tiles and the tiles that supply the recipe's fixed-site
input. The opening has iron ore supply on six tiles (Italy, Spain, Syria, Tunisia, Turkey, United Kingdom) and none in China, so the
newcomer is built on an ore tile, in the Mediterranean-and-Atlantic area that already holds four idle bloom makers
(`last_runs` nil from year 2). The plan is a sliver of their capacity, so Chinese bloom stays unmade there and the Chinese
buyers wait on carriage between areas. Fix lies with merchants carrying bloom (not entry) and with the makers' own
input chain, as the section above says.

## Measured: the late brick and cart surge is not a wear wave (branch 473-shelter-replacement-wave, no commit)

The opening seeds each durable at about flow times service life (`opening._seed_durable_stocks`, `households_orders._durable_ratio`),
a steady-state stock with no ages, and wear is exponential (`inventory.wear_moves`), so the stock cannot wear out at once.
In one Rome run the household brick stock declines smoothly after its early build-up, brick bids stay steady, and the
brick price does not run away; brick makers' output falls far below wear and nearly stops. Cart makers stop within the
first years and the cart price climbs without bound against standing replacement bids. The open question is why brick
and cart makers stop: carts lack iron bar (section above); bricks were not traced. Measured with scratch probes over
`spin_up_trace` (stocks, flows, bids and prices by year); no committed command exists.

## Measured: how the yearly rate is set, and what moves before it reaches its ceiling (branch 473-why-the-rate-hits-its-ceiling)

**The rule.** `economy.Economy._lend` (`sim/economy/economy.py`) gathers the year's loan requests (producers' `expand` and
`enter` plant, `state deficit`, households' `subsistence`, merchants' `trade`) and the funds on offer, and calls `credit.clear`
(`sim/economy/credit.py`). Each lender offers at a lowest rate; each request can pay at most its `maximum_rate` less its
risk premium. `labour.clearing_point` finds the rate where the two queues meet. The year's rate is then:

1. `sticky_move` from last year's rate toward that target by `RATE_ADJUSTMENT_SHARE_PER_YEAR` of the gap;
2. raised at once to the lowest lender ask if the sticky rate falls below it while some borrower would still pay it (the
   `base_rate < lowest_ask` branch in `credit.clear`), so a rise is not step-limited and a fall is;
3. held at `RATE_CEILING_SHARE` times the opening rate (`capital_market.py`), which is what the spike's 0.48 is.

With funds on offer and no requests, `_lend` moves the rate toward the lowest ask by the same step. Nothing but the households
offers funds in this run (no banks, firms or state), and a household offers its cash above its spending and cash target at
`HOUSEHOLD_TIME_PREFERENCE + expected_inflation` (`households_orders.py`). Expected inflation is each cohort's smoothed
year-on-year change of the basket price level (`households_close.close_year`, `currency.update_expected_inflation`).

**What the early years show.** Probe `rate473b`-style (scratch: a wrapper over `credit.clear` printing supply, lowest ask,
requests by purpose and unmet by purpose, one line a year, Rome first stage from the harness opening; not committed, no command
prints it), years 0 to 33: funds offered are one to two orders of magnitude above everything asked (offers of the order
1e10 against requests of the order 1e8 to 1e9 in money-supply units), the state asks for nothing, and the rate equals the
lowest ask to the digit in nearly every year (for example years 24, 30 and 33 jumped straight to it). So in the first
thirty-odd years the rate is not a clearing of plant, merchant or state credit against savings; it is the households' reservation
rate, time preference plus the smoothed change of the basket price level. A fall in the price level (a dozen years of deflation
from the opening) drove it to nil by year 9; a rise drives it up.

**The spike is not explained by that alone.** The trace dump (`rows60_6f00.json`, `spin_up_trace`, head 6f0085da) has the rate at
about 0.04 in year 45 and 0.48 in year 46, then 0.40, 0.33, 0.25, 0.22, 0.24, 0.20, 0.14, 0.10 by year 54. The price level
that precedes it rises from about 0.26 (year 43) to 0.30, 0.38 and 0.41, and the money supply falls smoothly through the whole run.
Smoothing those year-on-year changes at the declared speed gives an expected inflation under a quarter, not the 0.43 a lowest
ask at the ceiling needs. And a jump from 0.04 to the ceiling in one year cannot come from the step limit unless the target is
far above it. So either the cohorts' expected inflation differs from this reconstruction (the cohorts read the level at their own
close), or at year 46 the clearing target is demand-driven: borrowers with very large `maximum_rate` (producers' yearly return on
plant runs into the tens and hundreds in the early-year probe) outbidding a funds supply that has shrunk. The decay after the
spike (about a quarter of the gap a year) is the step limit toward a target that itself falls.
Unverified: which of the two; the probe stepping 46 years takes longer than the five minutes a subagent may run.

**Probe for the next run.** `scratchpad/rate473_full.py` wraps `credit.clear` and prints, per year, the price level, rate, money,
debt, cohorts' expected inflation (lowest and highest), supply, lowest ask, the unsmoothed clearing target, last rate, requests by
purpose with the share able to pay the clearing rate, money lent and any state request. Run it for 60 years from the repo root.
Reading it: `rate == lowest_ask` means the Fisher floor; `target` far above `lowest_ask` with demand able to pay exceeding
supply means credit demand; `state` non-empty means the treasury.

**Not changed.** No defect was proven, so no code changed. Candidate defects to judge once the probe is read: a rate that is
the households' reservation rate while supply swamps demand makes the credit market inert (the funds pool is almost all of
the money stock); the one-way step limit (instant rise to the lowest ask, slow fall) makes any one-year price jump a ratcheted
spike; unbounded `maximum_rate` from `unit_cost.return_on_capital` lets one cheap plant sale set the clearing price when supply is short.

## Measured: where the households' cash goes in the year of the rate spike (branch 473-where-household-cash-goes)

**Finding.** Households' cash is lent out, not lost. Before the year's plans, `lending.lend_working_capital`
(`sim/economy/lending.py`, called from `_run_year` in `sim/economy/economy.py`) lends every cohort's cash above its target to
the merchants whose carriers' wage loans (`carriage_hours.wage_loans`, `sim/economy/carriage_hours.py`) were asked at the last
close. In the spike year that single call moves households from about 2.1e10 to about 3.1e8; no other phase before
`clear_labour` changes household money. The loans are repaid in `_service_loans` at the year's end, which is why the total
is back (about 2.1e10) within the same year and the year-end figure of year 48 looks normal. So the drop is physical in the
book (money really changes hands, nothing is mis-counted), but the loan size is a sizing defect.

**Why the loan is that big.** `wage_loans` asked for the bill of every hour the merchant bid for, at the market's remembered
wage. The thin labour markets of the Algerian tiles offer a few thousand hours against tens of millions bid, so they clear at
the merchants' own reservation price, and the remembered wage runs away (it rises every year). The bill is wanted hours times
that wage, about 5.6e10 in the spike year against about 4.9e9 the year before, while the wages actually paid by merchants in
the year were about 6e8. The households' spare cash (about 2.1e10) is all taken, the funds left for the ordinary credit
round are about nothing, subsistence borrowing finds no lender and the rate goes to its ceiling.

**Command.** Load the year-45 pickle with the code of commit fed22775 and step twice; wrap `Book._record_money` (tally by
purpose, payer class, payee class) and the `_run_year` phases (household money before and after each). Script:
`scratchpad/a473/flow_probe.py` in the orchestrator's scratchpad.

| Phase of year 46 | Household cash before | after |
|---|---|---|
| `lend_working_capital` | 2.10e10 | 3.1e08 |
| `clear_labour` | 3.1e08 | 1.46e09 |
| `clear_goods` | 1.46e09 | 1.30e09 |
| `_service_loans` | 1.4e09 | 2.15e10 |
| `money_taxes` | 2.15e10 | 2.09e10 |

(Year 45 does the same at a smaller size: 2.14e10 to 1.64e10 in `lend_working_capital`.)

**Changed.** `wage_loans` sizes a merchant that had a crew plan last year on the hours the labour markets sold it
(`YearLedger.crew_hours_bought`, set in `dispatch_merchants`), shared among its keys of that market by their wanted hours.
A merchant without a plan is sized on the hours wanted, to no more than the market's whole supply last year (hours hired plus
idle, from `ledger.labour_results`); that bound is loose when several such merchants share one market. The runaway wage in the thin markets is a separate matter
and remains: bids far beyond the area's offered hours clear at the bidders' reservation price. Regression tests:
`WageLoanTests` in `sim/tests/test_economy_carriage_hours.py`.

**Checked.** The fix applied to the fed22775 code and the same pickle: the wage loans asked at the close of year 45 fall
from 5.6e10 to 1.9e09, `lend_working_capital` in year 46 moves households from 2.10e10 to 1.90e10 (it was 3.1e08), and the
households keep about 1.9e10 into the credit round. Not run: the full spin-up to year 48 (longer than five minutes), so the
rate and subsistence-borrowing figures of the later years are unmeasured.

## Measured: is the steady deflation the mint failing to replace worn coin? (branch 473-steady-deflation-and-zero-rate)

**Finding.** The money stock shrinks every year by about the coin wear, as the sections above say, but that shrinkage is far too small
to be the deflation. In a 15-year trace from a short-spin-up opening the stock falls about 13 per cent while the price level falls
about 55 per cent. What moves with the price level is the real economy contracting: hours employers take, producers' cash and real
output fall by large factors in the first five years while the households' cash rises. No code changed; no small general defect
was proven.

**Command.** `ROME_SPIN_UP_YEARS=3,2` and a probe that steps `AgentEconomy` the way `economy_port_trace.spin_up_trace` does and prints,
per year, the figures below (`scratchpad/p473_money.py` in the orchestrator's scratchpad; about 6 s a year, 15 years in under 100 s).
Note the opening is the 3,2-year short spin-up, not the declared-length one, because building the declared-length opening cold took
longer than five minutes; so the first-year contraction below may partly be the unsettled opening and the 60-year figures are
not reproduced here.

| Year | Price level | Money stock | Coin worn | Coin struck net | Households' cash | Cohorts' cash target | Producers' cash | Hours hired | Real output | Rate |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.645 | 4.07e10 | 4.11e8 | 0 | 2.09e10 | 1.3e8 | 1.86e10 | 1.44e10 | 3.59e10 | 0.174 |
| 1 | 0.686 | 4.04e10 | 4.08e8 | 1.1e8 | 2.43e10 | 9.5e8 | 1.46e10 | 5.99e9 | 1.22e10 | 0.050 |
| 2 | 0.629 | 4.00e10 | 4.04e8 | 1.3e7 | 2.57e10 | 7.5e8 | 1.27e10 | 3.57e9 | 5.6e9 | 0 |
| 4 | 0.502 | 3.91e10 | 3.95e8 | -2.0e7 | 2.78e10 | 6.6e8 | 9.0e9 | 2.81e9 | 1.4e9 | 0 |
| 7 | 0.369 | 3.80e10 | 3.84e8 | -9.8e6 | 3.02e10 | 7.3e8 | 6.2e9 | 3.21e9 | 1.4e9 | 0 |
| 10 | 0.334 | 3.68e10 | 3.72e8 | 3.8e6 | 3.09e10 | 1.14e9 | 3.6e9 | 3.56e9 | 1.7e9 | 0 |
| 14 | 0.314 | 3.53e10 | 3.56e8 | -3.2e7 | 3.31e10 | not printed | not printed | 4.47e9 | not printed | 0.025 |

Offered hours stay near 1.1e11 throughout, so about 97 per cent of the offered hours are idle after year 2. Cohorts' mean
expected inflation runs between -0.03 and -0.18 from year 1.

**Reading.**
1. Mint: it does not replace wear. Struck net is between minus 7e7 and plus 1.1e8 against wear near 4e8 (share of wear
   replaced about zero). The cause is the one already found above (Update 1 and 2): metal reaches the mint only from silver
   producers, whose output the declared deposits cap at a fraction of wear. `mint.mint_orders` bids for all the metal offered
   at the mint price; nothing in its decision starves it, so no change to `sim/economy/mint.py` is justified. Changing it to strike
   without metal would be a money-supply target, which the design forbids.
2. That shrinkage (1 per cent a year) cannot explain a price level falling 55 per cent in 14 years. The money is not lost
   from circulation but sits with households: their holdings are about 30 times their own cash target while spending is limited to
   income plus a capped drawdown (`households_orders.goods_orders`, `WEALTH_DRAWDOWN_LIMIT`), and producers' cash drains to
   them as the wage bill and sales collapse. So the price level follows demand from a contracting income, not the stock.
3. A reinforcing loop is visible but not isolated: `currency.cash_balance_target` takes the cost of holding money as
   `max(0, rate + expected inflation)`; at a zero rate and expected inflation below zero the cost is zero and the target is
   at its largest, so expected deflation raises the demand for cash exactly when the nominal rate cannot go below zero.
   Whether it matters was not measured (cash is already far above target here).

**Not found.** Why hours hired and real output fall by an order of magnitude after year 0 (producers' plans against falling prices
and a wage floor are the candidates; the probe did not print wages or plans). Whether the same holds on the declared-length opening
(the orchestrator's 60-year trace on the supply-curve labour cap shows the level recovering after about year 30). A one-year
spike of the rate to its ceiling between years 30 and 60 is not explained by this probe, which stops at year 14; the 46th-year spike
analysis above (wage-loan sizing, `lend_working_capital`) remains the lead.

## Measured: why output falls tenfold after the opening (branch 473-why-output-collapses-after-the-opening, deleted unmerged)

**Finding.** The producers and the labour market are not the cause; they follow sales. In the opening year the households
spend about 1 per cent of their cash and the producers sell about 0.3 per cent of what the opening sized them for, so the
whole of year 0's output goes into stock. From year 1 the stock gate (`producers.runs_for_stock`, `sim/economy/producers.py:367`)
binds for most producers and cuts planned runs to expected sales less the excess stock. Expected sales are rebased each year on
real sales, which are an order of magnitude below the opening's, so planned runs, hours hired and real output follow down. About
two thirds of the fall in output value from year 0 to year 2 is food staples, whose floors the households grow on their own
plots (Complaint 545). No small general defect was found, so no code changed beyond the cherry-picked drawdown fix.

**Command (about 25 s a run of 5 years; the probes are scratch, not committed).**
`ROME_SPIN_UP_YEARS=3,2 PYTHONPATH=. python3 <scratchpad>/p473_hh.py 5 out.json` wraps `producers.plan` and `producers.produce`
(binding limit, runs achieved), `households.goods_orders` and `year_goods._less_what_it_grew` (budget before and after the
own-plot cut), and captures the year's `YearLedger` (clearings, household bids). `p473_value.py out.json 22` prints the
per-good table. All three are in the orchestrator's scratchpad (`p473_split2.py`, `p473_hh.py`, `p473_value.py`).

**1. What falls (value of output at the first cleared price of each good; food staples dominate).**

| Good | Output value y0 | y1 | y2 | y3 | Share of the y0-to-y2 fall |
|---|---|---|---|---|---|
| millet | 6.0e9 | 1.6e9 | 6.5e8 | 9e7 | 31.5% |
| wheat | 2.9e9 | 7.7e8 | 3.8e8 | 9e7 | 14.7% |
| flour | 2.7e9 | 1.5e9 | 6.2e8 | 1.4e8 | 12.2% |
| starch | 1.3e9 | 7.2e8 | 1.8e8 | 8e5 | 6.7% |
| mechanical energy | 1.1e9 | 5.8e8 | 2.4e7 | 0 | 6.6% |
| stone blocks | 1.1e9 | 5.5e8 | 2.3e8 | 1.2e8 | 5.2% |
| common wine | 9.8e8 | 5.5e8 | 2.9e8 | 7.7e7 | 4.0% |
| olive oil | 1.0e9 | 6.5e8 | 3.8e8 | 1.7e8 | 3.9% |
| vegetables | 6.5e8 | 2.5e8 | 6.7e7 | 1.7e5 | 3.4% |
| total (all goods made) | 2.12e10 | 8.3e9 | 4.2e9 | 2.0e9 | 100% |

Food staples (millet through vegetables, with bread) are about three quarters of the fall; wool, milk, brick, shoes, linen are
about 1 to 2 per cent each. The by-products with no demand (manure, straw, nightsoil, clay) fall most in physical units but are
priced near nothing.

**2. What binds in `producers.plan`** (count of producers by the limit that sets the planned runs; hours lost = (capacity - plan) times hours per run).

| Year | Stock gate | Yearly change step | Land cap | Share working (price under cost) | Cash |
|---|---|---|---|---|---|
| 0 | none (no sales record) | none | none | 1855 producers, 6.0e9 h | 3718 producers, 2.9e9 h |
| 1 | 4841 producers, 5.8e9 h | 131, 1.2e9 h | 300, 9.7e9 h | 242, 8.4e8 h | 131, 1e8 h |
| 2 | 3038, 1.45e10 h | 2161, 2.6e9 h | 15, 1.6e9 h | 484, 9e8 h | 141 |
| 3 | 2684, 1.5e10 h | 2340, 2.4e9 h | 14, 1e9 h | 716, 6e8 h | 246 |

Cash and price (share working) are small throughout; the stock gate takes the largest share of lost hours from year 2 on, the yearly step
second. The land cap in year 1 is one block of 300 by-product and fuel producers (manure, straw, coal, wood).
In year 0 the cash limit shows because the producers' cash is small against the opening's plans; it cuts hours, but the achieved output
that year is still the highest.

**3. Year 0's output builds the stock that gates years 1 to 3.** For every staple and processed good, the stock a producer
holds when it plans year 1 equals its whole year-0 output: manure 8.07e10 held against 8.07e10 made, clay 8.8e9 against 8.8e9,
flour 3.79e9 against 3.79e9, wine 9.0e9 against 9.7e9, starch 1.29e9 against 1.29e9. The stock does not fall afterwards
(flour 3.8e9, 5.0e9, 5.9e9, 6.0e9 at the plan of years 1 to 4; wine 9.0e9, 1.2e10, 1.2e10, 1.1e10; starch 1.3e9 to 2.1e9),
because their sales stay far below the stock; nightsoil, clay and manure decay only slowly.

**4. The opening's assumed sales against the real ones.** Total traded value over all clearings, and the households' share:

| Year | Expected sales at expected prices | Traded value (all buyers) | Households' purchases |
|---|---|---|---|
| 0 | 4.5e10 | 1.4e8 | 1.35e8 |
| 1 | 1.4e10 | 4.9e9 | 3.4e9 |
| 2 | 8.8e9 | 4.0e9 | 2.8e9 |
| 3 | 5.5e9 | 4.5e9 | 3.4e9 |

By good, the opening's expected sales (units) against units traded:

| Good | Expected sales, year 0 | Traded y0 | y1 | y2 |
|---|---|---|---|---|
| common wine | 2.7e10 | 2.5e7 | 2.9e8 | 8.8e7 |
| flour | 7.8e9 | 7.6e6 | 9.2e8 | 2.0e7 |
| vegetables | 7.0e9 | 7e6 | 3.4e7 | 2.8e7 |
| olive oil | 3.4e9 | 1.5e7 | 1.1e8 | 1.1e8 |
| starch | 1.2e9 | 3.9e6 | 1.7e7 | 7.4e6 |
| bread | 2.4e9 | 3.2e8 | 5.2e8 | 1.8e8 |

Which assumption fails: it is Complaint 545, not 526 or 607. In year 0 the households' bids are all of their cash
(1.15e10, `smooth_rise` off while settling); then `year_goods._less_what_it_grew` (`sim/economy/year_goods.py:59`) cuts each floor
bid by the share of that floor grown on their plots, and the total bid budget falls from 1.15e10 to 3.9e8 (millet 1.76e9 to 1.1e7,
olive oil 1.47e9 to 9.5e6, brick 1.21e9 to 6e4, wheat, wine, flour, bread, starch alike, each cut by more than 99 per cent). The
opening (`sim/economy/opening.py:164`) sizes the same goods from the same function without that cut. In year 1 the cut is smaller
(1.74e10 to 1.26e10) because the bids are less floor-dominated, but the money is still not spent. The cut money is not redirected: households end year 0
with 2.1e10 in cash against a target of 1.3e8.

**5. Why the households' hoard still does not come back, with the spend-down fix in.** Households bid 1.26e10, 1.7e10, 2.0e10, 2.0e10
in years 1 to 4 after the cut, and buy 3.4e9, 2.8e9, 3.4e9, 4.3e9. The unspent budget by what happened at the market:

| Year | Supply exhausted (everything offered was sold) | Supply left unsold (price or ceiling) | No offer at all |
|---|---|---|---|
| 1 | 6.3e9 | 1.9e9 | 9.6e8 |
| 2 | 1.24e10 | 1.3e9 | 4.9e8 |
| 3 | 1.43e10 | 1.5e9 | 9.4e8 |
| 4 | 1.42e10 | 1.1e9 | 8.1e8 |

So about 70 per cent of the budget goes to goods whose whole supply sold out (coal, noric steel, bronze, brass, leather, opium,
firewood, brick, canvas, stone blocks, linen, timber: year 2 largest were coal 2.7e9, noric steel 2.3e9, bronze 1.4e9), while the
food that the opening made in surplus has no buyers. The drawdown fix lets the budget exist; the hoard is not spent because the
goods the budget names are thin (short chains for metals, land caps on fuel and timber, see the sections above), and the goods
that exist are not wanted. Households' cash still rises (2.27e10, 2.41e10, 2.55e10 at the plan of years 1 to 3).

**Not found / not checked.** I did not test whether re-sizing the opening's food by the own-plot share (tried and reverted above)
changes year-1 output now that the drawdown fix is in; that needs the joint by-product (bran) handled first. The 'supply
exhausted' classification compares the quantity traded with the quantity offered at the clearing price (`ClearingResult`), so it
counts a good whose price sits at a bidder's ceiling the same as one with no producer. Whether the thin metal and fuel goods are short for a recipe-chain
reason (inputs, land caps) or a plan reason was read only from the earlier sections, not re-measured here. The 15-year and
declared-length runs were not repeated.

**6. What stops makers from expanding to meet the spending** (same probe, `p473_short.py out.json <goods>`, makers grouped by main output; binding limit counted per maker in `producers.plan`).

| Good | Year | Planned / capacity | Achieved / planned | Binding (makers) | Traded |
|---|---|---|---|---|---|
| coal | 1 | 0.18 | 1.0 | stock gate 66, land 30 | 6.6e9 |
| coal | 2 | 0.28 | 1.0 | yearly step 100 of 104 | 2.6e9 |
| coal | 3 | 0.46 | 1.0 | yearly step 103 | 3.75e9 |
| canvas | 1, 2, 3 | 0.27, 0.45, 0.58 | 1.0, 0.95, 0.88 | stock gate 95, then step 100, 102 | 3.1e7, 2.2e7, 2.8e7 |
| noric steel | 1, 2, 3 | 0.23, 0.31, 0.18 | 0.41, 0.007, 0.36 | stock gate 98, then step 81, step 68 / share working 35 | 3.1e6, 7.9e4, 6.4e5 |
| bronze | 1, 2, 3 | 0.23, 0.43, 0.26 | 0.82, 0.45, 0.02 | stock gate 98, step 89, step 63 / share working 41 | 9.6e3, 3.9e3, 2.4e3 |
| leather | 1, 2, 3 | 0.34, 0.53, 0.27 | 0.83, 0.04, 0.11 | stock gate 90, step 103, step 104 | 1.0e7, 2.9e5, 3.5e5 |
| brick | 1, 2, 3 | 0.23, 0.02, 0.06 | 0.9, 0.8, 0.23 | stock gate 39, 38, 37 with share working 15, 35, 40 | 2.3e5, 5.1e5, 4.1e5 |
| firewood, timber | 2, 3 | 0.31 to 0.41 | 1.0 | step 55 to 58 of 88 / 93, land 2 to 3 | |

Reading, in the order a maker meets the limits:
1. Year 1: the stock gate. Year 0's unsold output is the stock; year 1's sold-out goods are the ones whose year-0 stock the households
   then bought (coal, canvas, steel, bronze, leather, stone blocks: traded in year 1 equals or exceeds the year's own output). The gate sees stock
   and low expected sales (`producers.py:367`) and plans well under capacity.
2. Years 2 to 3: the yearly change step (`within_a_years_change`, `producers.py:281`, `OUTPUT_CHANGE_SHARE_PER_YEAR`). The stock is gone, the
   price is up and the maker would plan more, but it may move at most a quarter of capacity from last year's runs, and last year's runs were
   the gated ones. With planned runs a third to a half of capacity in year 3, recovery to the demand takes several more years, over which
   the unspent household money keeps bidding the price up.
3. Metals and leather: planned runs are not reached. Noric steel achieves 0.7 per cent of its plan in year 2, bronze 2 per cent in year 3, leather 4 per cent
   in year 2: inputs (ore, bloom, charcoal, hides) are short, as the earlier sections found. Widening the plan there changes nothing until
   an input maker exists.
4. Cash is not binding in these goods; share working binds for about 40 of 104 bronze, brass and steel makers by year 3 (price under cost at the expected price).

The inflation the orchestrator saw over 60 years is consistent with this: the spend-down frees demand at the stock-adjustment pace while
supply can move only a quarter of capacity a year and, for chains, only as fast as the input makers do. Not tested here: raising
`OUTPUT_CHANGE_SHARE_PER_YEAR` (that would loosen the limit that stops chains from amplifying, per the earlier section) and the 60-year run.

## Measured and not merged: the opening sized net of the own-plot cut (branch 545-opening-sizes-for-bought-food, deleted unmerged)

Sizing the opening's producers with the year's own `_less_what_it_grew` (through a new `opening_own.less_what_it_grows`)
makes opening and year agree by construction, but on the short opening it lowers traded value and output further and
the stock gate still dominates later years. Settling income on the cut demand collapses the economy toward nothing (the
526 collapse). The root is the year's own-plot rule: every unhired hour goes onto a plot with unlimited free land, so
households grow nearly all their staples and buy almost none. Land-limited own plots (Complaint 551, branch
`551-households-farm-the-plots-they-hold` (deleted unmerged; its code is lost)) are needed before the opening can be sized sensibly. Measured with
`ROME_SPIN_UP_YEARS=3,2 PYTHONPATH=. python3 <scratch probe p473_hh.py> 5 out.json` on each commit; the probe is not
committed.
