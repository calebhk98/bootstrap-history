# The agent economy

Status: being built on branch `economy-dynamic-markets`. Measure the old model's static-price share with
`python3 sim/market_trace.py rome_100ad 30`; this design exists because nearly every good there stays
within a few percent of its opening cost.

## What it is

`sim/economy/` is a standalone package: agents that hold money and goods, markets that clear their
orders, and the money they pay with. It imports `sim.world` and `sim.constants`, never `sim.engine`.
The engine reaches it only through `sim/engine/economy_port.py`; the tech tree, the founder, projects
and screens ask the port questions (a price, a wage, a rate, what a concern takes) and post
transactions. `sim/tests/test_economy_imports.py` holds both rules.

Contracts: `sim/economy/types.py` (records) and `sim/economy/protocols.py` (the year order and what
each module offers).

## Choices and why

**Annual step, clearing within the year.** Inventory-target price rules assume many ticks a year; at
one tick a harvest failure would show as rationing at last year's price and a spike only a year later.
So each market clears within the year at the price where buyers' schedules meet sellers' offers, and
the dynamics come from what carries between years: stocks and the reservation prices their holders
set, output decided on last year's price (a cobweb lag), producers idling and exiting, cash balances,
debts and the money stock.

**Buyers' schedules carry a floor and a budget.** `Bid.quantity_at(price)` is a floor (what is needed
whatever the price) plus a part that falls with price, capped by what the buyer can pay. With no
seller the price rises until budgets bind, so there is no price ceiling or floor constant: a famine
price is the price at which the poorest cohort's money runs out, and the unmet floor is recorded for
demography to read.

**Sellers' reservations follow their situation.** A producer offers new output at no less than its
variable cost; a holder of stock at what it expects to get next year less carrying cost and spoilage; a
seller short of cash for debts or wages below that; a waste product below zero.

**Clearing order follows the recipes.** A good clears after the goods it is made from, so producers
sell this year what they made from inputs bought this year. Cycles draw their inputs from stock.

**Money is a stock with holders.** Purses are accounts in `accounts.Book`; the money supply is their
sum. Agents keep a target cash balance against their spending; holding more than the target raises
spending and prices, less lowers them, so velocity is an outcome. The target falls as expected
inflation rises, which is what lets an issuer printing to cover a deficit run into hyperinflation.
Coin is struck from metal at the mint's terms and melted when the metal is worth more than the coin,
so the price of the metal in coin stays near the mint's parity and the price of goods in coin follows
money demand against the stock. Mining cost is the floor below which mines close. The opening money
stock is derived: what the opening agents want to hold at the seeded prices.

**Space is tiles.** Regions are being deleted. A good's market area is the set of tiles between which
carriage costs less than a share of its value, so silver trades across a civilisation and grain within
a tile or a few.

**Stock-flow consistency.** Every movement of money or goods has a counterparty. Money and goods enter
or leave only through named edge accounts (`types.EDGE_*`). Engine postings that do not yet name a
payer or payee are booked against `edge:legacy`, whose volume is measured and should fall to zero.
Complaint 382 lists them.

**Start.** A hidden spin-up runs the economy from the opening population, land, techniques and the
solver's costs until prices settle, cached per civilisation and seed.

**Other countries** trade as external sellers and buyers booked against `edge:external`; the types
allow them to become full economies, and later players.

## Heuristics

Every adjustment speed, cash-balance target and expectation rule is declared with
`sim.constants.declare(kind="temporary_heuristic")` beside its use. `python3 sim/constants.py --kind
temporary_heuristic` lists them.

## Validation

Distributions over civilisations and seeds, never dated events: wage-to-grain ratios in a plausible
band, grain more volatile than metals, harvest shortfalls raising grain prices in the same year, a metal
influx raising the price level with a lag, inflation rising with an issuer's printing, and money
conserved every year.
