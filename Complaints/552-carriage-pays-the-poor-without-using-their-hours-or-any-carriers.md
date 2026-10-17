# Carriage pays the poor without using their hours or any carriers

**Status:** partly fixed. Carriage hours are now hired in the labour market (below); carts, ships and animals as capital, travel time and storage along the route stay open.

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

## Done: carriage hours are hired

- `sim/economy/carriage_hours.py`: a merchant bids, in the year's labour market and before any goods move,
  for the crew hours its shipments need, on the tiles its goods left, in the carrier trade of the cheapest
  land mode that needs no built way. Hours come from geography's crew hours per tonne-km (the setup's
  `carriage_crew`), over that mode's money rate: crew hours per unit of carriage money. The bid is last
  year's dispatched shipments (the merchants' plan, before any cut): this year's purchases are known only
  after the labour market clears. A merchant that has not shipped has no plan and is not limited.
- `merchants.dispatch` cuts every route by the same share when the hours hired fall short, and the fee is
  paid less the crew's wages, which the labour market has already paid to the households that sold the
  hours. Those hours are no longer offered to other employers or left for the household's own plot.
- Still a shortcut: the rest of a fee (feed, carts, ships, animals, losses) goes to the poorest
  households of the source tile; sea and river hauls count at the land mode's hours; handling hours are
  not counted. Capital for carriers with service lives, and dispatch limited by it, are not built.
- Carriers must exist to be hired: the opening places people by the runs producers expect, so no carters
  exist when merchants first ship, and the labour core does not grow a new trade fast enough (measured
  below). The crew hours are therefore bid in the unskilled trade (`CARRIAGE_CREW_UNSKILLED_SHARE`, a
  labelled heuristic retired by 556), not the mode's carter or sailor trade. A merchant that ships nothing
  in a year has no plan, so is not limited, the next.
- Carriers are paid at the labour market, before the year's lenders meet, so a merchant with no cash in hand
  could not pay its hired hours and they were not delivered. A merchant now asks, at the year's close, for
  a one-year working-capital loan for next year's carrier wages (`carriage_hours.wage_loans`), staked as
  capital like its other loans. Bids are placed where people live: goods leaving an empty tile are bid for
  in the merchant's home labour area.
- Open: the carriage rates are priced at the opening wage while the unskilled market wage in a spun-up
  game is a small fraction of it, so the crew's pay is a small part of each fee and the rest of the fee still
  goes to the source tile's households. One wage for both is not yet done.
- Tests: `sim/tests/test_economy_carriage_hours.py`.
