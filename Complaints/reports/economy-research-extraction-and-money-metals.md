# Research brief: mine economics and money metals for the economy layer

An input report, written by a research agent from web searches during economy round four. Key:
**[S]** means confirmed in a search snippet (URL given); **[M]** means from background knowledge,
not re-verified, so treat it as a lead. The web tools returned thin results. The Cambridge paper
on ancient gold/silver ratios could not be read, and no price-series volatility table was found.

## 1. Extraction in an annual model

- **Pre-modern mining is mostly Ricardian, not Hotelling [M].**
  - Reserves were large against the flow that could be reached. Labour, drainage, ventilation and
    smelting fuel bound output, not the ore stock.
  - Depletion shows as rising cost per tonne, not as a scarcity premium.
  - So: price a metal at the full cost of the marginal working site, and let depletion reach the
    economy as a yield or capacity change that geography hands in.
- **Entry and exit hysteresis.**
  - Dixit 1989 [S] (https://ideas.repec.org/p/fth/prinec/91.html): the entry trigger sits above
    variable cost plus interest on the sunk entry cost, and the exit trigger below variable cost
    minus the exit cost.
  - The band is wide even for small sunk costs, and widens with uncertainty.
  - Brennan & Schwartz 1985 value a mine with open, idle and abandoned states [S, snippet only].
- **A rule we can implement:**
  - Three states: working, idle (care and maintenance, which costs upkeep) and closed.
  - Working to idle: the smoothed margin is below zero for a window.
  - Idle to closed: the owner will not pay the upkeep.
  - Idle to working: the margin covers variable cost plus the annualised restart cost.
  - A producer with negative equity for several years is liquidated.

## 2. How others split the layers

- Victoria 3 [S, snippets: exputer.com gold-mine guide, steamcommunity discussion]: discoverable
  resources per state cap the building levels, and the market sets prices and employment.
- Europa Universalis has static goods income [M]. Factorio and Anno patches deplete, and operators
  move on [M]. CGE models use a sector-specific fixed factor, which gives Ricardian rising cost
  [M].
- **Interface:**
  - geography owns the site, its capacity cap, its yield (which falls with extraction), any idle
    damage, and discovery;
  - the economy decides whether to work a site, hires, pays and prices;
  - the economy reports extraction and idle years back to geography.

## 3. Money metals

- **Mint band.** A mint that buys at parity less its charge and sells at parity bounds the
  bullion price between the two while coin is convertible [M].
- **Gresham and bimetallism** [S: moneyness.ca on Locke; newtonandthemint.history.ox.ac.uk
  MINT00322 on Newton 1717]. The metal overvalued at the mint flows in; the undervalued one is
  hoarded, melted or exported.
- **Stocks dominate flows.** Today's gold stock is about 58 years of mine output [S:
  gainesvillecoins.com, ainsliebullion.com.au; modern figures]. Price is set by willingness to
  hold the stock, not by the year's mining.
- **Gold/silver ratio**, from weak popular sources [S: learn.apmex.com, a substack]:
  - Rome about 12;
  - medieval Europe 8-14;
  - China about 10.

  To verify against DOI 10.1017/S0959774323000355 (not read). A ratio below 1 is a bug.
- **Non-monetary demand.** Ornament and plate act as a stock sink that releases metal when prices
  are high [M].

## 4. Volatility ordering

- Grain prices move with harvests: r ≈ -0.41 against the previous summer's temperature in a
  European panel [S: ideas.repec.org/a/eee/eecrev/v170y2024ics0014292124001818].
- Expected ordering [M, not sourced]: grain > base metals > precious metals in coin.
  - Metals are durable, with large stocks and slow supply.
  - Metals swinging more than grain is a sign that their prices are formed on small flows.
- Data to compute the real coefficients: the Allen-Unger commodity dataset
  (b2find.eudat.eu/dataset/322ed5f6-1df5-562c-9f89-9ee94f8cd5fb); Brunt & Cannon
  (ideas.repec.org/a/eee/exehis/v58y2015icp74-92).

## Ranked recommendations (agent's)

1. **A mint standing bid holds the price flat for the backing metal.** Price each money metal
   through its own mint.
   - Risk: it hides scarcity, and needs a capacity cap.
2. **An idle, close and reopen state machine with a hysteresis band**, used for every producer's
   exit.
   - Risk: flicker if the smoothing is short.
3. **Price metal at the marginal working site, with holders' stocks (hoards, plate) buffering
   flow.**
   - Risk: a buffer that is too elastic flattens prices for ever.
4. **A bimetallic flow driven by the gap between the mint ratio and the market ratio.**
   - Risk: lock-in to one metal looks like a bug, though it is historically right.
5. **An ensemble check of the volatility ordering** (grain > base metals > silver; gold/silver
   ratio in a band, never below 1).
   - The bands must be measured from data before use (rule 4.2).
