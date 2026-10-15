# The agent economy's spin-up never settles, so the opening is a point on a cycle

**Status:** partly - the money stock is sustained (Update 4, `spin_up_money_supply` passes); the spin-up still does not settle: the price level and wage drift for decades because the labour market clears far below the cost table's wage (Update 4)

Found while tracing why the opening money wage moved several-fold between builds of the same branch (the
fix for that is in `Complaints/closed/470`). The price level in the hidden spin-up cycles with a period of
about twenty-five years (one Rome trace: about 0.94 at the start, 2.7 a dozen years on with the interest rate
over twenty per cent, back near 1 by year twenty-four), the first stage does not meet its convergence tolerance
within its years, and the game opens wherever the cycle stands. Unrelated changes (a producer's expansion rule,
the smoothing bound) moved the opening price level and the money wage by a large factor through that alone.

The cause is not households' opening money: they open at their cash-balance target, the producers' working
capital passes to them in the first year whatever the opening cash was, and scaling households' opening cash
or income up or down on the small fixture (`sim/tests/economy_fixture.py`, which cycles the same way) changes
nothing. The mismatch is between the opening income, which assumes every worker is employed all year at the
opening wage, and producers sized to a much smaller final demand: realised income is a fraction of the opening
figure, and producers' expansion and hiring against idle labour drive the cycle.

Why it matters: every price, wage and purse a player sees at the opening depends on where the cycle stops,
so a small change to any mechanism can move the whole opening economy, and a measurement taken at the opening
says little about the mechanism measured (CLAUDE.md 4.2: the baseline should be a plausible draw, not an
accident of when the warm-up stopped).

Evidence: build a game with `sim.tests.harness.sim(capital=400000.0)` and print `game.capital` (the founder's
purse is repriced by the opening money wage, `sim/engine/opening_money.py`) on two builds that differ only in
an unrelated rule; print the spin-up's price level, households' cash over the wealth they keep, and spending
over income by spin-up year (no committed command prints these).

A longer trace (Rome, the first stage run for a couple of hundred years with no tolerance met) shows the
cycle sits on a drift that does not end. At the opening most of the hours households offer go unhired;
producers borrow and expand for decades and the hired share climbs, and the unskilled wage falls the whole
time. Capacity and the hired share level off after several decades, but the economy does not: the money
supply shrinks every year by about the coin wear (`metal_stock.COIN_WEAR_PER_YEAR`), the mint strikes almost
nothing to replace it (its edge nets to about nothing, and some years it melts), the wage keeps falling, and
after the better part of a century households start going short of food and the price level climbs by
multiples. The money audit (`money_audit.year_report`, `YearOutcome.money_audit`) shows the wear edge as
the only steady sink. So a longer spin-up cannot settle it, and the shipped openings (`openings/`, written by
`simulator.py openings`) are the declared-length spin-up, not a resting point. No committed command prints
the trace; it is each year's `YearOutcome` from `Economy.step` during the spin-up.

What it would take: an opening whose producers' capacity, workforce and households' income agree (sized from
the same final demand), and a model of how fast producers expand and hire against idle labour that damps rather
than overshoots; coin lost to wear replaced (new metal reaching the mint when coin is scarce) so the money
supply does not drain; then a spin-up that runs until its tolerance is met, or records plainly when it is not.

Related: 470 (closed), 472 (closed), 464.

## Playtest evidence (Rome, `play --civ rome_100ad --kit merchant --seed real25`)

The cycle reaches the player. Over the first two decades the `money` screen's market rate moved from single
digits to the ceiling `bounded_rate` sets (four times the civilisation's `starting_interest_rate`,
`sim/world/capital_market.py`), and stayed there for several years. Over the same years "funds lenders hold"
fell to about a quarter of its year-104 figure. Funds lenders hold is built mostly from `household_saving()`
(`sim/engine/economy_capital_market.py`), so household saving collapsed. The founder's borrowing is far too
small to move it. A founder who had borrowed at a normal rate to hire staff paid well over half the debt in
interest each year and went insolvent. Wages (and with them the workshop's revenue, which is a markup on
wages) fell through the same years. Reproduce by stepping a year at a time and reading `money`.

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

