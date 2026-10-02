# The agent economy against published economy models

Review, 2026-10-02, of `sim/economy/` (the default economy) for complaints 385, 387, 388, 390, 392 and
393. Sources: a full code read of the package, the open complaints, a literature survey (sources at
the end), and measurements. Every figure here carries the command that produced it.

## How a year runs

`Economy.step` (`sim/economy/economy.py`) runs these steps in order:

1. Producers plan from last year's prices.
2. The state plans its budget.
3. Labour clears per trade and tile at a sticky wage, and wages are paid at once.
4. Hours nobody hired go to households' own plots, up to their food floor.
5. Households bid from cash that now includes this year's wages.
6. Credit clears.
7. Merchants place their orders.
8. Goods clear one good at a time, inputs before outputs. Each (good, area) solves for the price where
   a falling, budget-capped demand meets a step supply of reservation prices.
9. The year closes: the mint, debt service, carriage, taxes, plant building, dividends, entry and
   exit, coin wear and the price index.

Dynamics come from what carries between years: stocks, expectations, cash, debts and the money stock.

## Where it matches good practice

| Practice in the literature | Here |
|---|---|
| Every payment has a payer and a payee (Godley-Lavoie stock-flow consistency; Caiani et al. 2016) | All money and goods move through one `Book`. They enter or leave only through named `edge:*` accounts. |
| Households follow a buffer-stock rule, spending more when they hold more (Lengnick 2013) | Households have a cash target and spend half the gap to it each year. The target falls as expected inflation rises. |
| Demand has a subsistence floor and a budget (Stone-Geary) | Needs carry floors and budget weights. Within a need, goods substitute at a constant elasticity. Bids are capped by cash, so a famine price is where the poorest run out of money. |
| Wages and rates are sticky, not instant (K+S, Mark-0) | Each closes 30% of the gap to its clearing level a year, and the wage never stays below every worker's ask. |
| Entry and exit are tied to finances (CATS) | Entrants stake owner cash and borrow at most that stake. Producers mothball after repeated losses and close when they hold nothing. |
| Heuristics are labelled and measured | Nearly every constant in the package is declared `temporary_heuristic` (`python3 sim/constants.py --kind temporary_heuristic`). `python3 sim/economy_validate.py` checks distributions over seeds, not dated events. |

Clearing within the year instead of using inventory-feedback posted prices departs from most
macro ABMs. `docs/architecture/ECONOMY_AGENTS.md` justifies it: at one tick a year, a harvest failure
would otherwise show up a year late. That reasoning holds, and this review does not recommend changing
it. Its cost is speed (complaint 390), because every (good, area) runs a root-finder every year.

## Where it falls short

Measured baseline: `python3 sim/economy_validate.py --years 30 --seeds 1,2`, about 6 minutes.

| civ | grain_vola | metal_vola | wage_kg_wh | money_drift |
|---|---|---|---|---|
| england_1300 | 0.16-0.17 | 0.22-0.41 | 0.25-0.27 | -0.011 |
| han_china_100ad | 0.14-0.23 | 0.27-0.32 | 0.29 | -0.012 |
| mexica_1500 | 0.09-0.11 | 0.15-0.17 | 0.10 | +0.02 |
| norse_900ad | 0.13-0.15 | 0.57-0.67 | 0.33-0.36 | -0.005 |
| rome_100ad | 0.11 | 0.53-1.18 | 0.13-0.14 | -0.003 to +0.005 |

### 1. The conservation check cannot fail

`check_money` sums every account, including the `edge:*` ones, so it is zero by construction. The
residual column above reads about 1e-15 for that reason, not because nothing leaks. Caiani et al.
make the per-sector transaction-flow matrix their test. The equivalent here is a per-edge
reconciliation: what each edge may move, and which edges must move nothing.

### 2. Bookkeeping defects

Each was found in the code read and checked line by line.

- **Unpaid labour is delivered.** An employer short of cash pays part of its wage bill but still
  receives every hour it bid for, and produces with them.
- **Duties on trade collect nothing.** Customs on imports and exports collect zero in all five
  civilisations, because the facts they are assessed on are never filled.
- **The rate cannot rise for lack of lenders.** When there are borrowers and no lenders, credit returns
  early: the rate never rises, and a stale expansion list blocks entry.
- **The mint mislabels and miscounts.**
  - Seigniorage is charged on the quantity of metal bought, not on what the mint paid for it.
  - Coin that leaves the country takes no metal with it, so the gap is booked as wear.
- **Plant is counted twice in the loss test.** In a year a producer buys plant, the plant counts both
  as a cost and as a capital charge.
- **Dividends go to one cohort.** Every dividend goes to the richest cohort of the tile, and the
  ownership shares are unused.

### 3. Metals swing more than grain everywhere (387)

This happens in every civilisation, not only Rome and Norse. In the literature, durable goods are
smoothed by competitive storage (Williams and Wright; Deaton and Laroque): someone buys when the price
is below the expected price less carrying cost, and sells when it is above. Nobody in the agent
economy buys a good to hold it. Merchants only carry goods between places, and producers only hold
back their own output against a target of three months of sales. A thin metal market therefore has no
buyer of last resort and no buffer.

### 4. Money drains without trade (385)

England and Han lose about 1.1% of their money a year. That is the 1% `COIN_WEAR_PER_YEAR` with
nothing bringing coin back. Hume's price-specie flow only stabilises if the other side exists. The fix
needs either partner economies (data) or a rest-of-the-world buyer and seller wired in the engine port.
Both are outside `sim/economy/`.

### 5. Land has no price (393)

`land_hectare_years` is not an input to any recipe (`sim/economy/recipes.py`), so land earns no rent,
and free entry drives grain to its labour cost. A scratch measurement (a Rome game run for five years,
summing `land_per_run × capacity_runs` per tile) found the following:
- Producers on most tiles use 2-6% of the tile's arable hectares.
- The anchor tile, where entrants are placed, can hold more than its arable area: `spain_03` held 1.7
  times its arable hectares.
- Rome has about 2.1 arable hectares per person.

So scarcity rent would be near zero on most tiles. Rent would come mainly from differences in land
quality inside a tile (Ricardo's differential rent) and from overfilled anchor tiles. A second cause
is in the data: the wheat recipe is 577.5 kg per hectare-year for 150 hours, with no seed or draught
input. At bare labour cost that is several kilograms of grain per hour of work, far above the 0.1-0.4
kg in the table.

### 6. Unskilled wages (388)

An hour buys 0.10 kg of wheat in Mexica and 0.13-0.14 kg in Rome. That is about half of England and
Han, and a third of Norse. Whether this is wrong needs sourced day wages against grain prices. The
figures available to this review were from memory, so they are not used. The mechanisms to check are
the wage floor (family subsistence per working hour), own-plot hours, and items 2 and 5 above, which
both move the cost of grain relative to labour.

## What was fixed on this branch

(Filled in when the fixes are merged; see the measured before/after table below.)

## Outside `sim/economy/`, not attempted

- 385 needs partner data, or a rest-of-the-world wired in `sim/engine/economy_port_year.py`.
- 392 needs more than one currency per economy, which needs per-civilisation data.
- Recipe inputs (seed, draught animals) are in `data/production/`.
- Moving metal with coin that crosses the border needs the port.

## Sources

The survey agent checked the citation metadata, not the full papers. Its formulas for CATS, K+S,
EURACE and Victoria 3 are from memory.

- Lengnick, "Agent-based macroeconomics: a baseline model", JEBO 86 (2013): https://ideas.repec.org/a/eee/jeborg/v86y2013icp102-120.html
- Caiani et al., "Agent based-stock flow consistent macroeconomics: towards a benchmark model", JEDC 69 (2016): https://researchinnovation.kingston.ac.uk/en/publications/agent-based-stock-flow-consistent-macroeconomics-towards-a-benchm-4/
- Gualdi, Tarzia, Zamponi, Bouchaud, "Tipping points in macroeconomic agent-based models" (Mark-0): https://arxiv.org/abs/1307.5319
- Brughmans and Poblome, MERCURY, JASSS 19(1):3 (2016): https://www.jasss.org/19/1/3/3.pdf
- Godley and Lavoie, *Monetary Economics* (2007); Williams and Wright, *Storage and Commodity Markets* (1991); Deaton and Laroque, "On the behaviour of commodity prices", RES (1992). These are cited from knowledge, without fetched links.
