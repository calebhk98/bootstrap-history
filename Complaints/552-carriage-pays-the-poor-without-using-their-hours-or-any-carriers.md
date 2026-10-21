# Carriage pays the poor without using their hours or any carriers

**Status:** partly - split into 627, 628, 629, 630, 631, 632 (all closed); closes when a real-game trace shows carrier trades answering the bids

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
- Done (632, closed): the rest of a fee is paid by supplier: the carriers worn and the animals' feed are bought in the goods market, the remainder stays with the merchant that owns the carriers. Only a first-year merchant's unhired crew pay still goes to the poorest.
- Dispatch limited by the fleet (631, closed; `carriage_fleet.py`, `carriage_fleet_book.py`, `sim/tests/test_merchant_fleet.py`): a merchant holds carriers in its carrier account, ships no more than their wear a year bears plus idle fleets it hires from other merchants, buys the fleet its routes call for, and carriers age by service life.
- Carriers must exist to be hired: the opening places people by the runs producers expect, so no carters
  exist when merchants first ship, and the labour core does not grow a new trade fast enough (measured
  below). The crew hours are therefore bid in the unskilled trade (`CARRIAGE_CREW_UNSKILLED_SHARE`, a
  labelled heuristic retired by 556), not the mode's carter or sailor trade. A merchant that ships nothing
  in a year has no plan, so is not limited, the next.
- Carriers are paid at the labour market, before the year's lenders meet, so a merchant with no cash in hand
  could not pay its hired hours and they were not delivered. A merchant now asks, at the year's close, for
  a one-year working-capital loan for next year's carrier wages (`carriage_hours.wage_loans`, sized after the owners took their profit, since the cash left is what pays), staked as
  capital like its other loans. Bids are placed where people live: goods leaving an empty tile are bid for
  in the merchant's home labour area.
- Hours follow the route (627, closed): `CarriageTable.haul` gives the money a tonne pays on each mode's legs
  and the handlings into each mode; `carriage_hours.Crew` turns a mode's leg money over its rate into the
  tonne-km it stands for, times that mode's crew hours (sea and river modes included, `carriage_crew`), and
  adds the setup's handling hours (`carriage_handling`, unskilled trade) for each handling into a mode whose
  handling the rates price. A merchant's plan, bids, hires and wage loans are keyed by (trade, tile).
- Wages by area: the rates are priced at the wage of the opening (`EconomySetup.carriage_wage`). Each year the
  carriage table is multiplied (`CarriageTable.set_scale`, no rebuild, exactly one where the wages are the one
  priced) by the change in the labour part of last year's carried flows, each priced at the wage of the area
  the goods left; the crew is paid that area's wage. Feed, carts and animals keep their price.
- The crew is still bid in the unskilled trade (`CARRIAGE_CREW_UNSKILLED_SHARE`), so a sailor's hours are
  labourer hours until 556 places people in the trades the flows need; the code bids each mode's own trade
  when that share is lowered.
- Tests: `sim/tests/test_economy_carriage_hours.py`, `sim/tests/test_carriage_hours_by_route.py`.

## Done: carriers are durable goods (629, closed)

- Cart, pack saddle and river barge are goods with recipes (`data/production/99_carriers.json`); merchant ship, ox and
  mule carry a `carrier_use` too, and all have sourced service lives in `data/world/service_lives.json`.
- `sim/economy/carriage_wear.py`: a tonne-km on a mode wears each carrier of its team by the team's count over
  (service life x days a unit works a year x tonne-km the team moves a day). A merchant keeps carriers in its own
  account; feed is used up by the tonne-km, a carrier with a life ages by it (see 631 below). The fee it pays
  the households of the source tile is less what those carriers cost at last year's price.
- Exposed for 630: `Merchant.carrier_wear` (units by good), `Merchant.carrier_team_days` (by mode), and geography's
  `carriage_rates` entries carry `carriers`, `tonne_km_per_team_day`, `team_payload_tonnes`.
- Done (631): wear limits dispatch and merchants open with fleets (below). Still open: on a real opening only carts and
  pack animals are supplied in the first years (no shipwright or saddler trade exists to answer the bids).
- Tests: `sim/tests/test_carriage_wear.py`.

## Sized (no change made)

- **Travel time is covered.** `sim/economy/merchants_transit.py` holds a haul for the whole years its days span, books
  spoilage each year to `EDGE_SPOILAGE`, charges interest in `gap_cost_per_unit`, and lags news; held by
  `test_merchant_travel_time.py`.
- **Storage at stages** is charged for the years a haul is held beyond the first (628, closed).
- **Carriers as capital** need, in order: cart, pack saddle and vessel goods with recipes and sourced service lives
  (only `ox` and `mule` exist, without service lives); carrier-days, animals per carrier and vehicle wear exposed on
  geography's `Rate` and threaded through `carriage_crew`; a per-merchant fleet whose yearly capacity follows from
  its carriers and the route's days, with bids or hire for more and wear booked from the service life (merchants are
  not worn today, `inventory.wear_moves` wears cohort holdings only); and an opening endowment of fleets. Several
  sessions in all.

## Split

Children, in order of work:

- 627: Carriage hours count sea and river hauls at the land mode's hours, skip port handling, and use one national wage
- 628: Storage at stages of a haul is not charged
- 629: Carts, pack saddles and vessels are not goods and have no service lives (closed)
- 630: Geography's rates do not expose carrier-days or vehicle wear (closed)
- 630: Geography's `Rate` does not expose carrier-days, animals per carrier or vehicle wear
- 631: Merchants have no fleet: dispatch is limited by cash, not by carriers
- 632: The non-labour part of a carriage fee (feed, carts, ships, animals, losses) goes to the poorest households of the source tile

552 stays `partly`: carriage hours are already hired (see Done).
