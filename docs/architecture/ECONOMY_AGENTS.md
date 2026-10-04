# The agent economy

Status: the game's economy by default. A game opts out with `cfg["agent_economy"] = False`;
`ROME_AGENT_ECONOMY=0` (off) or `=1` (on) overrides either way (`switch_requested`,
`sim/engine/economy_port_year.py`). Tests of the old economy's own mechanisms opt out explicitly.
The yearly economy checks measure it against plausible ranges.

## What it is

`sim/economy/` is a standalone package: agents that hold money and goods, markets that clear their
orders, and the money they pay with. It imports `sim.world` and `sim.constants`, never `sim.engine`.
The engine reaches it only through `sim/engine/economy_port*.py`; the tech tree, the founder, projects
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

**Wages and the interest rate are sticky.** Each moves by a share of the gap to its clearing level a
year, but a wage is never left below every worker's ask while an employer would pay it, and a wage
nobody offered hours at stays where it was. With savings on offer and nobody borrowing, the rate drifts
toward lenders' lowest ask. A goods market that traded nothing keeps its price unless every seller
asked more than any buyer would pay; an offer that is only float residue is no supply.

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
a tile or a few. Carriage is the carters' pay: it goes as wages to the poorest households of the tile
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
above subsistence, more when the real rate is high (`households_orders.savings_target`); what they hold
beyond buffer and spending is offered to borrowers. Loans are claims in the lender's wealth
(`credit_claims.py`): a default is the lender's loss and cuts its spending. Producers borrow for plant,
merchants for cargo their cash cannot buy, households for a shortfall with income ahead.

**Demand brings makers.** Where buyers wanted more of a good than was sold, beyond what its makers'
idle capacity could have added, a recipe the society knows that pays at the price bid starts or grows
the tile's producer of it (`entry.py`, `entry_year.py`), its owner staking cash and borrowing plant
only up to that stake. Owners refill paying producers that ran out of working cash; a producer with no
capacity, plant coming or debt closes. A good with no known recipe gets no maker.

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
