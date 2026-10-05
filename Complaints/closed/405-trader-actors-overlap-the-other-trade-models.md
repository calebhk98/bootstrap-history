# Trader actors carry goods abroad without moving the partner's market, beside two other merchant models

**Status:** closed - folded into 115

Traders (`sim/agents/trader.py`, `trader_entry.py`) buy where a good is cheap and sell where it is
dear, when the gap pays freight, interest and risk. Places are the home society and each foreign
economy (`sim/engine/agents_port_trade.py`). Three gaps remain:

- **The partner's market never moves.** A sale abroad does not enter the partner's market book
  (`EconomyState.foreign_market_book`). A gap the traders serve therefore never narrows, and they
  carry the same cargo every year, up to the depth share. In a Rome start traders carry stone
  blocks and linen to Han from the first year. Measure it with a Rome game: run `advance_actors`
  and print each trader's `routes`. There is no command for this yet.
- **Three models of merchants.**
  - `sim/engine/foreign_traders.py` already moves an aggregate merchant flow on the same routes.
  - `sim/economy/merchants.py` moves goods between tiles inside the agent economy.

  The actor traders add to both. One should own each flow.
- **No domestic routes.** The engine does not expose prices per market area, so trader actors
  trade only between countries.

What it would take:
- A trader's shipment books into the partner's market book through the foreign-economy code.
- The aggregate `foreign_traders` flow becomes the sum of trader actors' cargo, or the reverse.
- An economy-port member exposing area prices, so traders can own domestic routes.
