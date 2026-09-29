# Prices use long-run cost, not the current market

**Status:** open

## What is wrong

The price solver prices a good at its long-run cost of production, including a
mine's up-front cost spread over its whole lifetime output (amortisation). A
real price is set by the market now: current supply against current demand,
with sunk costs playing no part once a mine is dug.

- A mine that produces most of its ore in its first decade floods the market
  then, and the price should fall then and recover later, not sit at an
  average over a century.
- Capacity that does not exist yet (a dam that will make cheap aluminium in
  ten years) should not lower today's price.
- A windfall of stock (every household finds iron in their room) should drop
  the price at once, with no production change.
- Money: each civilisation's money is tied to its coin metal, valued at the
  metal's cost at the opening technology and then frozen. A modern silver or
  gold mine that floods the market should lower the metal's value and so the
  coin's, which is inflation (as with New World silver in early modern
  Europe). Today it does not.

## What economists use

Exhaustible resources are usually modelled with spot prices set by marginal
extraction cost plus a scarcity rent (Hotelling), stocks and flows cleared in
a market each period, and investment decided by expected revenue against
up-front cost. Sunk costs matter to the decision to build, not to the price
afterwards. See `docs/architecture/ECONOMY_MODEL_SURVEY.md`.

## What it would take

- Keep the solver's long-run cost as a reference and a starting quote.
- Add a per-period market for each good: supply from existing stocks and
  current production capacity of every actor, demand from households and
  producers, price clears between them.
- Use amortisation only in the decision to build (quotes, payback), not in
  the market price.
- Revalue each civilisation's money from its coin material's market price
  each period, so metal gluts cause inflation and shortages deflation.
