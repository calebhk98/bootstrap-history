# The agent economy, round four

Follows `agent-economy-review-round-three.md`. Again only `sim/economy/`, new tests and new files in
`Complaints/` could change; what needs other folders is filed as complaints 410-418.

## How it was measured

- **Whole games:** a scratch driver replaying the deleted `sim/economy_validate.py` (`git show
  97473f1:sim/economy_validate.py`). It plays 30 years per civilisation and seed and adds gold, silver
  and iron columns. No committed command prints these yet (Complaint 416). The figures are now pure
  functions in `sim/economy/diagnostics.py`, ready for that command.
- **Caution on seeds:** they still share one spin-up per civilisation (Complaint 400), so a seed is
  not an independent draw.
- **Caution on cached spin-ups:** the spin-up cache is keyed on source, so a monkeypatched experiment
  silently reuses a spin-up computed by other code. Every variant has to be a real source edit in its
  own checkout. An early A/B in this round was wrong for that reason and was redone.
- **Mechanisms:** tested on a new engine-free three-tile economy (`sim/tests/economy_fixture.py`,
  `run(setup, years)`). Ten years take well under a second, so scenario tests no longer need the
  engine.

## What was wrong, and is fixed

- **Every producer sat on its market's anchor tile, while each tile is its own labour market.**
  - In the fixture, people off the anchor earned almost nothing and missed most of their food floor.
  - Producers are now spread over a market's tiles by working hours at the opening, and newcomers go
    to the cheapest tile that can staff them (`location.py`).
  - Test: `economy_location`.
- **Exit never happened.**
  - `close_agents` ignored `exited` and "mothballed" instead, resetting the loss count, so nothing
    ever left.
  - Plantless capacity (mines, most workshops) never shrank, so idle capacity flooded back on any
    price spike.
  - Now: plantless capacity follows use; a producer with no variable margin after its loss years
    exits, and its cash repays its lenders before its owner takes the rest (`producers_close.py`,
    `producer_exit.py`).
  - Tests: `economy_exit`.
- **Mines could not be sited.**
  - Deposits are geography's. The economy takes `SiteLimit`s (capacity and yield per recipe and
    tile) and reports `YearOutcome.extraction` (`sites.py`).
  - Until the port is wired (Complaint 411), sited recipes keep today's placement under the
    declared heuristic `UNSITED_EXTRACTION_ANYWHERE`.
- **Crops grew in any climate.**
  - Cacao, Mexica's money and a food, filled highland tiles.
  - Recipes now carry the data's `grown_in_climate_classes`; tiles carry their Koppen class;
    `sites.climate_allows` gates opening and entry.
- **Stuck chains and accidental monopolies (398, 387).**
  - England's iron chain held a few tonnes of capacity after the spin-up. Bar iron then sold at
    hundreds of times its input cost, because:
    - plantless producers cannot borrow to grow;
    - entry fired only where buyers were turned away;
    - entrants were sized to last year's trade, which was grams.
  - `entry_margin.py` lets a lasting margin draw newcomers. Each market's cheapest recipe sets an
    entry price (its full cost plus a band). Where the price stays above it for as many years as a
    loser waits to exit, newcomers are sized to:
    - what the year's bids would take at that price (a floor stays a floor; spending beyond it is
      unit-elastic);
    - less the capacity there and coming;
    - at the incumbents' growth pace;
    - and only where buyers would spend at least as much at the lower price.
  - A market with buyers and no maker gets a trial newcomer whatever its stale remembered price says.
  - Tests: `economy_entry_margin`, `economy_no_offer_markets`.
- **Audit fixes:**
  - near-zero rates no longer make plant bids unbounded (annuity over the plant's life);
  - plant goods not used by the capacity built stay in stock;
  - the mint no longer trades with itself;
  - a no-demand price respects the offer floor;
  - land rent is continuous in the land used, instead of flipping at band edges (393);
  - a partner's export order no longer freezes the home price memory (found by a new 389 test);
  - the hunger need and unskilled trade come from the setup.
- **Tests:** the 19 round-three scratch tests are in the suite (396). Agent-economy equivalents
  cover the state budget, the loanable rate and foreign balances (389, partly). The economy has a
  published surface, `api.py` (Complaint 410 holds the port patch), with hours-weighted trade wages
  for 394.

## Measured, 30 years, seeds 1-2

- **Rows:**
  - "baseline" is the branch start (`d9e3295`);
  - "exit and location" is `ee5a42f`;
  - "tip" is the branch tip, with margin entry taken out and the trial newcomer, the cost memory
    and the durables spending cap in.
- **Command:** scratch driver (Complaint 416).
- **Spin-up:** seeds share one spin-up (400), so read the ranges as indications.

| | grain vol. | iron vol. | wage, kg wheat/h | hungry | gold/silver |
|---|---|---|---|---|---|
| england, baseline | 0.08-0.19 | 0.36-0.41 | 0.27 | 0-0.0005 | ~930 |
| england, exit and location | 0.05-0.13 | 0.14-0.30 | 0.41 | 0 | ~6 |
| england, tip | 0.12-0.22 | 0.27-0.38 | 0.55-0.63 | 0.0004-0.005 | ~5700 |
| norse, baseline | 0.12-0.19 | 0.32-1.35 | 0.27 | 0.001 | ~3500 |
| norse, tip | 0.10-0.17 | 0.25-0.28 | 0.46 | 0.001-0.002 | ~4e4 |
| rome, baseline | 0.07-0.08 | 0.36-0.39 | 0.16 | 0.009 | ~148 |
| rome, tip | 0.06-0.08 | 0.24-0.25 | 0.25 | 0.004-0.005 | ~7700 |
| mexica, baseline | 0.10 | n/a | 0.09 | 0.005 | ~1300 |
| mexica, exit and location | 0.07-0.08 | n/a | 0.14 | 0.05-0.09 | ~7000 |
| mexica, tip | 0.06-0.12 | n/a | 0.04-0.05 | 0.02-0.03 | ~8e4 |
| han, baseline | 0.08-0.14 | 0.20-0.23 | 0.31 | 0.004 | ~2000 |
| han, tip | 0.04-0.08 | 0.23-0.28 | 0.33-0.34 | 0.012 | ~1.4e4 |

Reading it:
- **Iron and metal swings** fell in England, Norse and Rome, and the Norse outliers are gone.
- **Wages:** the wage in wheat rose in England, Norse and Rome, and fell in Mexica, where wheat is a
  minor food (Complaint 388).
- **Grain** is steadier than the baseline in Rome, Norse and Han. In England it swings more than with
  exit and location alone.
  - An ablation (one switch at a time, seed 1) puts most of that on the trial newcomer and some on the
    durables spending cap.
  - Without the trial newcomer, Mexica's hunger roughly doubles, so it stays.
  - Grain volatility of 0.12-0.22 may be historical (`economy-research-staple-volatility.md`, from
    memory), but England's harvest correlation weakened. Part of the swing is the economy's own
    cycling: the first thing to fix next round.
- **Hunger:**
  - Mexica's rose with exit and location (wheat makers left the cacao-rented highlands), and the
    climate gate, the cost memory and the trial newcomer brought it down again, still above the
    baseline.
  - Han's is above its baseline and has not been traced.
- **Gold** is wrong everywhere, and its ratio to silver moved further off at the tip: Complaint 413 (gold valued like silver per kg, no store-of-value
  demand) and 414 (no good is durable in the economy). The store-of-value design is built and tested
  on the fixture (`households_store.py`; `agent-economy-store-of-value-design.md`). It is inert until
  the port passes service lives (414). Opening stocks and its behaviour checks (steps 6-7) remain.

## Found by the full suite after merging main

- **The full suite:** 6324 checks, 10 failures. Six fail on main too:
  - `automation_audit` and `complaint_45_forest_area_not_region_count` crash at import;
  - `capital_charge` raises `KeyError: 'lab'`;
  - one timing check in `complaint_141_year_cost`.
- **The other four (`quote_matches_charge`, `ventures_lifecycle`) were this round's.** Rome's bar iron
  after the spin-up cost about ten times main's, so a project's materials outran the test's cash.
- **Cause:** idle plantless capacity decayed even when its runs would pay. A chain short of an
  input (bar iron short of bloom) lost its hands, so its price rose and it sold less.
- **Fix:** idle capacity now decays only when its runs would not pay.
- **Result:** Rome's bar iron at the start is about 730 denarii a kg against main's about 400. Both
  are far above its cost of making, which is the stuck chain of Complaint 398.

## Tried and not merged

- **Remembering a rising price where buyers bid and nobody offers.** A household's budget for a good
  is planned from that good's remembered price, so the buyers' reach is circular and the memory
  barely moved. The trial-newcomer rule above replaced it.
- **Margin entry sized by the bids' budgets.** At a much lower price those budgets buy far more
  than buyers would, most of all for staples. Grain volatility rose to 0.3-0.4 and the wheat wage to
  several kg an hour.
- **Margin entry without the elasticity condition, or with a smaller share or a wider band.** Grain
  volatility stayed at 0.19-0.38.
- **Margin entry with the elasticity condition** (`b81201d`, taken out in `4babb5a`).
  - **Ablation** (England and Norse, seed 1, one variant switched off at a time, each a real source
    edit with its own spin-up cache): margin entry alone raised grain volatility from about 0.08 to
    0.18 (England) and from 0.11 to 0.21 (Norse), lowered the wage and added hunger. The climate gate,
    land continuity, the foreign-bid fix and the trial branch did not.
  - **What entered** (England seed 1, every plan logged; spin-up and game together): household
    organic and fuel goods such as milk, wine, firewood, peat, coal, starch, olive oil and fat. Most
    are land recipes competing with wheat for rent. Wheat itself barely entered, and the iron chain's
    plans were near zero runs.
  - **Buyers:** households, about 98% of the projected spending; merchants were not the cause.
  - **The gate was nearly vacuous.** Treating surplus spending as unit-elastic let it pass for almost
    every plan. Entry prices sat far below market, perhaps because land rent at the anchor tile
    understates the cost of a land recipe.
  - **Organic entry alone reproduced the instability. Mineral entry alone kept grain steady but
    swung metals.**
  - **Next attempt, for the next round:**
    - gate on observed spending growth;
    - treat goods in a floor chain or using land as staples, with a Nerlove planted-area response
      and rent in the entry cost;
    - keep a mineral path only for a lasting, observed shortfall.

## Left to do

- Complaints 411-417 (port, geography and data).
- 413/414 (gold and durables).
- 392 (several moneys: design in `agent-economy-several-moneys.md`).
- 106 (banks: design in `agent-economy-capital-markets.md`).
- 385 (needs an owner decision).
- 395, 391, 399 (data).
- 390: speed is not the bottleneck now. An England year is about 0.3 s of economy, and the engine
  side costs about as much.
