# Economic levers, demographics, and material inventory need to be actionable

**Type:** Economic simulation / discoverability  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `buy farm`/`buy housing`/a named trade school all exist (`_cmd_buy`, `sim/engine/proto/dispatch.py`); a `materials` command/report now covers "stocks on hand, annual production and demand, and current buy/sell values for every tracked material." See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player concern

The household could not directly expand food production or worker housing to
change the cost of living, nor establish a school for a named trade to make
that profession more common. Population and trade demographics were difficult
to connect to those actions. Material extraction was presented mainly as annual
throughput, with no clear inventory, valuation, purchase, or sale surface.

## Why it matters

Without these levers, endogenous wages are mostly something that happens to the
player rather than a market they can influence. Without a visible durable stock,
a mine also appears to waste every unused tonne and to care only about this
year's production even when earlier surpluses should cover later demand.

## Expected behavior

Allow investment in food, housing, and trade-specific schooling; keep the
existing population report discoverable; and expose durable material stocks,
annual production/demand, current buy and sell values, and explicit trading.
