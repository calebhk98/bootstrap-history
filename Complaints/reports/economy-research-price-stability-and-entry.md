# Research brief: stable annual clearing, thin metal markets, margin-driven entry

An input report, written by a research agent from web searches during economy round four. Key:
**[read]** means the source was read in full; **[snippet]** means only a search summary was seen;
**[memory]** means the agent's own recollection or derivation, not verified. EURACE, JAMEL, CATS
and K+S rule details could not be retrieved.

## 1. How discrete-period ABMs keep prices stable

- **Lengnick 2013** [read]
  (legacy.econ.tuwien.ac.at/lva/compeco.se/artikel/jebo_2013_agent_based_macroeconomics_a_baseline_model.pdf):
  - firms react to inventory held against demand, using fixed bands, with small random price and
    wage steps;
  - firm count is constant, with no entry or exit;
  - households trade with a few firms only.
- **Mark-0** (Gualdi, Tarzia, Zamponi, Bouchaud; arxiv.org/abs/1307.5319) [read]:
  - price and output adjust by a few percent, conditioned on demand against output and price
    against the average;
  - the main instability is the asymmetry between hiring and firing speeds;
  - a bankrupt firm is replaced next step at the average price and output.
- **Common pattern:** signals come from inventory against demand, not from price against cost.
  Steps are small. Entry replaces exits one for one, with entrants sized to the incumbent average.
  None of these models uses margin-driven entry.

## 2. Cobweb

- Naive expectations are stable only when supply is less price-elastic than demand [read:
  en.wikipedia.org/wiki/Cobweb_model].
- Adaptive expectations widen the stable region (Nerlove) [snippet].
- With expectation weight λ, stability needs supply elasticity / demand elasticity < 2/λ − 1
  [memory, the agent's derivation].
- Metals are the worst case: floor-dominated, inelastic demand meets supply that is elastic over a
  narrow range.
- Stockholding damps cobwebs by moving supply across years (Williams-Wright) [memory].
- Damping that does not tune outcomes acts on what planners know: an anticipated own-price impact,
  λ set from the slopes, and capacity under construction counted as supply.

## 3. Thin markets

- Victoria 3 sets price from the ratio of buy to sell orders around a base price, and trade moves
  local prices toward import parity [snippet: Paradox dev diaries 9 and 54].
- Principled bounds [memory]: substitution in the bid, an import-parity ceiling from freight,
  and budget-derived reservations.
- Fixed bands around a base price are a price table in disguise (CLAUDE.md 4.5).

## 4. Entry

- Dixit 1989 trigger band [snippet]. Hopenhayn 1992 entry to zero expected value [snippet].
- Mankiw-Whinston 1986: free entry overshoots, because new firms take business from old ones
  [snippet].
- The likely cause of our own overshoot [inference]: every would-be entrant saw the same gap, and
  capacity under construction was not counted, so the gap fired again.
- **A rule we could implement** [the agent's own synthesis]:
  - enter only above average cost times (1 + band), and exit below variable cost times (1 − band),
    with the band following realised volatility;
  - size added capacity as gap / (demand slope + incumbent supply slope);
  - subtract the capacity pipeline first;
  - cap entry as a share of capacity, symmetric with expansion.

## 5. Performance [memory]

- Piecewise-linear schedules: a sorted-breakpoint cumulative sum, then `searchsorted`. This is
  exact, with no bisection.
- Vectorise across goods, store as struct-of-arrays, and re-sort only the markets whose orders
  changed.

## Ranked recommendations (agent's)

1. **Count the pipeline, and size entry by the slope-adjusted gap.**
   - Risk: slopes are noisy in thin markets.
2. **A hysteresis band for entry and exit, scaled by volatility.**
   - Risk: a band that is too wide means margins are never competed away.
3. **Set the expectation weight from the elasticity ratio.**
   - Risk: noisy slopes.
4. **Bound thin markets by substitution and import parity**, derived from engine state.
5. **Make the output-change speeds symmetric, and carry stock over between years for durables.**
