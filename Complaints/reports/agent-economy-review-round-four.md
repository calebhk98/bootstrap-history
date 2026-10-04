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
| england, tip | 0.12-0.15 | 0.40-0.49 | 0.37-0.38 | 0 | ~1500 |
| norse, baseline | 0.12-0.19 | 0.32-1.35 | 0.27 | 0.001 | ~3500 |
| norse, tip | 0.12-0.19 | not re-measured | 0.40-0.43 | 0.0001 | ~4e3-1.6e4 |
| rome, baseline | 0.07-0.08 | 0.36-0.39 | 0.16 | 0.009 | ~148 |
| rome, tip | 0.05-0.07 | 0.29-0.30 | 0.23 | 0.0007-0.0009 | ~1300 |
| mexica, baseline | 0.10 | n/a | 0.09 | 0.005 | ~1300 |
| mexica, exit and location | 0.07-0.08 | n/a | 0.14 | 0.05-0.09 | ~7000 |
| mexica, tip | 0.07-0.10 | n/a | 0.22-0.23 | 0 | ~1000-1100 |
| han, baseline | 0.08-0.14 | 0.20-0.23 | 0.31 | 0.004 | ~2000 |
| han, tip | 0.07-0.12 | 0.23-0.34 | 0.38-0.39 | 0.003-0.005 | ~7e4 |

Reading it (tip measured after the idle-capacity fix below; seeds 1-2):
- **Better than the baseline:**
  - Rome: grain, iron and hunger, and a higher wage.
  - England: grain steadier, with the harvest correlation back near the baseline's; a higher wage;
    no hunger.
  - Han and Norse: higher wages.
- **Worse than the baseline:**
  - (Mexica's hunger, about 0.13 at the previous tip, is fixed. Cacao is both Mexica's money and a
    food, and the mint for a money with no issuer bought up to a whole money stock of beans a year at
    parity, so growing money always paid and took the food land. Money with no issuer is now
    monetised only as holders want more cash, plus what is lost
    (`economy-research-commodity-money.md`). Mexica's hunger is now 0 in both seeds, its money no
    longer grows by itself, and its wage is above the baseline.)
  - Iron swings more in England and Norse than at the baseline. Its level is still far above cost,
    the stuck chain of 398.
- **Gold** is wrong everywhere: Complaint 413 (valued like silver per kg, no store-of-value demand)
  and 414 (no durable goods in the economy). The store-of-value mechanism is built and tested on the
  fixture (`households_store.py`; `agent-economy-store-of-value-design.md`) and is inert until the
  port passes service lives (414). Opening stocks and behaviour checks (steps 6-7) remain.
- **The trial newcomer** was the main cause of England's grain swing before the idle-capacity fix.
  Whether it still is, and what it does for Mexica, needs re-measuring.

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
