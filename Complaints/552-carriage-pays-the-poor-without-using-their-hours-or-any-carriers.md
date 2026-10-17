# Carriage pays the poor without using their hours or any carriers

**Status:** open

Found by an outside reviewer reading the repository; checked against the code.

- `dispatch_merchants` (`sim/economy/year_close.py`) pays the carriage as wages to the poorest
  household of the tile the goods leave. Its docstring calls this a shortcut until carriers hire
  hours in the labour market. The hours are not taken from that household's labour.
- Merchant dispatch is limited by cash, not by a fleet, pack animals or a carrier workforce.
- Purchases go into the next year's selling regardless of route length (517 covers distance and price
  information).

So trade can be paid for and still be physically impossible, and the labour market never sees the
demand for carters, sailors and porters (530).

## What it would take

- Carriage as a productive activity: hours of carters, sailors and porters hired in the labour
  market, carts, ships and animals as capital with service lives, and dispatch limited by both.
- Shipments with a travel time from the route (`sim/geography/` already computes pace), charged
  storage, spoilage and financing for that time. Stanford's ORBIS model separates duration, cost, mode
  and season and is a benchmark for the Roman case.
