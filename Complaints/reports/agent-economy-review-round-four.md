# The agent economy, round four

Follows `agent-economy-review-round-three.md`. Again only `sim/economy/`, new tests and new files in
`Complaints/` could change; what needs other folders is filed as complaints 401-408.

## How it was measured

- **Whole games:** a scratch driver replaying the deleted `sim/economy_validate.py` (`git show
  97473f1:sim/economy_validate.py`). It plays 30 years per civilisation and seed and adds gold, silver
  and iron columns. No committed command prints these yet (Complaint 407). The figures are now pure
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
  - Until the port is wired (Complaint 402), sited recipes keep today's placement under the
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
  published surface, `api.py` (Complaint 401 holds the port patch), with hours-weighted trade wages
  for 394.

## Measured, 30 years, seeds 1-2

Baseline is the branch start (`d9e3295`). "Exit and location" is commit `ee5a42f`. "Now" is the
branch tip. Rome is shown for seed 1 only where a run was not repeated.

| | grain vol. | iron vol. | wage, kg wheat/h | hungry | gold/silver |
|---|---|---|---|---|---|
| england, baseline | 0.08-0.19 | 0.36-0.41 | 0.27 | 0-0.0005 | ~930 |
| england, exit and location | 0.05-0.13 | 0.14-0.30 | 0.41 | 0 | ~6 |
| england, now | 0.18-0.22 | 0.14-0.18 | 0.28 | 0.002 | ~2600 |
| norse, baseline | 0.12-0.19 | 0.32-1.35 | 0.27 | 0.001 | ~3500 |
| norse, now | 0.20-0.21 | 0.19-0.31 | 0.67 | 0.0001-0.001 | ~2e5 |
| rome, baseline | 0.07-0.08 | 0.36-0.39 | 0.16 | 0.009 | ~148 |
| rome, now | 0.12-0.13 | 0.09 | 0.13 | 0.008-0.02 | ~800-1600 |
| mexica, baseline | 0.10 | n/a | 0.09 | 0.005 | ~1300 |
| mexica, now | 0.09-0.10 | n/a | 0.07 | 0.017-0.033 | ~2800 |
| han, baseline | 0.08-0.14 | 0.20-0.23 | 0.31 | 0.004 | ~2000 |
| han, now | 0.17 | 0.19-0.21 | 0.34 | 0.001-0.004 | ~400 |

Reading it:
- Iron and metal swings fell everywhere and the Norse outliers are gone.
- Grain swings more than with exit and location alone. Whether that is margin entry or another
  change is being measured; this section is updated with the answer below.
- Mexica's hunger is worse than the baseline and is being traced.
- Gold is still wrong everywhere: Complaint 404 (gold valued like silver per kg, no store-of-value
  demand) and 405 (no good is durable in the economy). Neither is a market-clearing defect.

## Tried and not merged

- **Remembering a rising price where buyers bid and nobody offers.** A household's budget for a good
  is planned from that good's remembered price, so the buyers' reach is circular and the memory
  barely moved. The trial-newcomer rule above replaced it.
- **Margin entry sized by the bids' budgets.** At a much lower price those budgets buy far more
  than buyers would, most of all for staples. Grain volatility rose to 0.3-0.4 and the wheat wage to
  several kg an hour.
- **Margin entry without the elasticity condition, or with a smaller share or a wider band.** Grain
  volatility stayed at 0.19-0.38.

## Left to do

- Complaints 402-408 (port, geography and data).
- 404/405 (gold and durables).
- 392 (several moneys: design in `agent-economy-several-moneys.md`).
- 106 (banks: design in `agent-economy-capital-markets.md`).
- 385 (needs an owner decision).
- 395, 391, 399 (data).
- 390: speed is not the bottleneck now. An England year is about 0.3 s of economy, and the engine
  side costs about as much.
