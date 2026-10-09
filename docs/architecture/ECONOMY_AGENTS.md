# The agent economy

Status: the game's economy by default. A game opts out with `cfg["agent_economy"] = False`;
`ROME_AGENT_ECONOMY=0` (off) or `=1` (on) overrides either way (`switch_requested`,
`sim/engine/economy_port_year.py`). Tests of the old economy's own mechanisms opt out explicitly.
The yearly economy checks measure it against plausible ranges.

## What it is

`sim/economy/` is a standalone package: agents that hold money and goods, markets that clear their
orders, and the money they pay with. It imports `sim.world`, `sim.constants` and the walled packages' `api.py` (geography, labour), never `sim.engine`.
The engine reaches it only through `sim/engine/economy_port*.py`; the tech tree, the founder, projects
and screens ask the port questions (a price, a wage, a rate, what a concern takes) and post
transactions. `sim/tests/test_economy_imports.py` holds both rules.

Contracts: `sim/economy/types.py` (records) and `sim/economy/protocols.py` (the year order and what
each module offers). Outside code imports only `sim/economy/api.py`, the package's published surface
(`docs/architecture/PACKAGE_WALLS.md`). The port reads the map from the engine's geography (the base map
with the active mods' overlays, `sim/engine/geography_port.py`) and hands the economy its tiles and that map
through the setup.

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

**Wages come from the labour core; the interest rate is sticky.** The economy keeps its workforce as
the labour core's `MarketState` (people per tile, trade and ability band; `labour_state.py`) and each
year hands the core the producers' bids as tranches of falling value (`labour_bids.py`), the outside
option, entrants and attrition from demography, and routes to bordering tiles (`labour_inputs.py`).
The core sets every (trade, tile) wage and trains, switches and moves people (sim/labour/market/DESIGN.md);
`year_labour.py` settles what it reports. A trade's training premium is whatever wage draws enough able
people to it. The interest rate moves by a share of the gap to its clearing level a year, drifting
toward lenders' lowest ask with savings on offer and nobody borrowing. A goods market that traded nothing
keeps its price unless every seller asked more than any buyer would pay; an offer that is only float
residue is no supply.

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
a tile or a few. The cost of a haul between tiles is geography's route cost (`sim/economy/tile_costs.py`
asks `route_costs`, see `sim/geography/INTERFACE.md`): rivers, coasts, grade and sea lanes come from the
map, and the economy supplies only its money per tonne-km for each mode. Carriage is the carters' pay: it goes as wages to the poorest households of the tile
the goods leave, until carriers hire hours in the labour market.

**Stock-flow consistency.** Every movement of money or goods has a counterparty. Money and goods enter
or leave only through named edge accounts (`types.EDGE_*`). Engine postings that do not yet name a
payer or payee are booked against `edge:legacy`, whose volume is measured and should fall to zero.
Complaint 382 lists them.

**Money takes each society's own form.** A civilisation's coin standard names its regime: struck coin
(a mint buys metal at parity less its charge and strikes it; the charge is the issuer's seigniorage),
weighed metal (money is the metal by weight, no issuer), or a commodity (cacao beans). The mint holds
a real metal stock, sells only what it holds and strikes only what it buys (`mint.py`), so mined metal
raises the money stock and, with a lag while it sits with savers, prices.

**The state spends what it raises.** Its revenue buys hours and goods in the same markets as everyone
(`state_budget.py`); a deficit is covered by its policy's order of borrowing, issuing (fiat) or
debasing (struck coin) (`state_finance.py`, `state_policy.py`). Printing to cover a deficit that grows
with prices runs away.

**Households save and lend.** Beyond their cash buffer they keep savings worth years of their income
above subsistence, more when the real rate is high, but never below a floor, so expected inflation reaching the rate does not
make them spend their savings (`households_orders.savings_target`). Wealth above target is spent down at a limited pace
(`WEALTH_DRAWDOWN_LIMIT`, set by the larger of this and last year's income), and a year's spending falls by at most
a limited share of expected spending (`SPENDING_CUT_LIMIT`), so a swing in the target does not swing demand for
durables; what they hold
beyond buffer and spending is offered to borrowers. Loans are claims in the lender's wealth
(`credit_claims.py`): a default is the lender's loss and cuts its spending. Producers borrow for plant,
merchants for cargo their cash cannot buy, households for a shortfall with income ahead.

**Demand brings makers.** Where buyers wanted more of a good than was sold, beyond what its makers'
idle capacity could have added, a recipe the society knows that pays at the price bid starts or grows
the tile's producer of it (`entry.py`, `entry_year.py`), its owner staking cash and borrowing plant
only up to that stake. A market with buyers and no maker in its area draws a trial newcomer judged at
its own full cost plus a margin, since its remembered price is stale (`entry_trial.py`). A good with no
known recipe gets no maker. Every recipe that pays draws a newcomer, best first, each for a share of
what the better ones leave: no cap on newcomers per market a year. Where makers exist and sellers have
raised asks until buyers are no longer turned away, a market whose usual (smoothed) price stays above
its cheapest recipe's entry price for as many years as a loser waits to exit draws newcomers sized to
what the bids take at the entry price, no faster than incumbents change their output
(`entry_margin.py`); the first attempt at this destabilised staple prices
(`Complaints/reports/agent-economy-review-round-four.md`, "Tried and not merged").

**Workers ask what they can sell for, down to a floor.** A worker's ask falls while hours go unsold
and rises when demand outruns supply (`sim/labour/market/asks.py`). It never falls below what keeping
his household alive and working costs (the need basket's floors at local prices) less what its own plot
grows (`labour_ask_floor.py`). `simulator.py economy-check` prints the hired share, the wage over that
floor and the staple's price over its labour cost.

**Producers sit on tiles.** Each tile is its own labour market, so a producer hires only its own tile's
people. At the opening a recipe's capacity is spread over its market area's tiles by working hours;
a newcomer goes to the tile where a run costs least (wages, land rent, carriage of the output to the
area's anchor, over the site's yield), among tiles with a site and idle hands to staff it
(`location.py`). Crops grow only on tiles of the climates their data names, and a site-bound recipe stays
inside the runs and yield geography declares per recipe and tile (`sites.py`); the economy models no
deposit and reports what it extracted so geography can deplete.

**Producers leave.** A producer whose year did not cover its costs and plant charge counts a loss year;
after enough of them, with no variable margin left, it exits: its cash repays its lenders first, the
rest and its goods go to its owner, and what the cash could not repay is the lenders' loss
(`producers_close.py`, `producer_exit.py`). Plantless capacity (mines, most workshops) follows use, so
idle hands are let go instead of flooding back on a price spike; a producer whose capacity has
dwindled to nothing, with no plant coming and no debt, closes (`entry.producers_to_close`).

**Prices that have not traded are not market prices.** Each market remembers how long ago it cleared;
the price index counts only goods traded recently, and the game shows an untraded good at its cost
of making at live prices, or flags it stale (`notional.py`). A
year's trade moves a remembered price in proportion to its volume against the market's usual volume, so
a sliver of trade at a freak price does not become the price everyone plans from.

**Start.** A hidden spin-up runs the economy from the opening population, land, techniques and the
solver's costs until prices and the interest rate settle, cached on disk per civilisation (keyed on
the data and source).

**Other countries** trade as external sellers and buyers booked against `edge:external`, at the
partners' prices. The year's trade settles in the partners' coin ledgers (`foreign_payments`), so a
partner paying out coin sees its prices fall, and it spends at most a share of the coin it holds
(price-specie flow). The types allow partners to become full economies, and later players.

**Trader actors' cargo** is not booked against `edge:external`. Each cargo leg that touches home gets an account in
the book (`sim/engine/economy_port_cargo.py`): a landing cargo arrives over the partner's own edge
(`external_edge(partner)`) and is offered, a taking cargo is bought with funds the trader put in; after the clear the
account's money goes back to the trader's purse over `edge:cargo` and the goods nobody took return over the
partner's edge. The partner's side settles in that partner's coin ledger and the route's carriers
(`sim/engine/trader_cargo.py`), and the trader's purse is trued up from its decision-time booking to the result.
The trader's purse itself is still the engine's, not an account in the book (Complaint 382).

**The founder's concerns sell in the same markets**, offered at their output's cost at the economy's
own prices and wages; the takings return to the engine's purse through `edge:legacy` (Complaint 382).

## Heuristics

Every adjustment speed, cash-balance target and expectation rule is declared with
`sim.constants.declare(kind="temporary_heuristic")` beside its use. `python3 sim/constants.py --kind
temporary_heuristic` lists them.

## Validation

Distributions over civilisations and seeds, never dated events: wage-to-grain ratios in a plausible
band, grain more volatile than metals, harvest shortfalls raising grain prices in the same year, a metal
influx raising the price level with a lag, inflation rising with an issuer's printing, and money
conserved every year.
