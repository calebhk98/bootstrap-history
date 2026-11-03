# The agent economy

Status: the game's only economy. There is no switch: a civilisation that holds no tiles is refused when the game
is built, and the engine's own opening figures answer only while the economy opens (`sim/tests/harness.py unopened_sim`
builds a game that stays in that state, for tests of the opening figures). The yearly economy checks measure it
against plausible ranges (`python3 sim/simulator.py economy-check`).

Open problems that touch this document are collected in `Complaints/964` (what the labour and goods re-audit left, one national price
rule) and `Complaints/507` (prices and traded volumes have two owners,
`ONE_PRICE_OWNER_PLAN.md`); where a section below describes a rule under repair it says so.

## What it is

`sim/economy/` is a standalone package: agents that hold money and goods, markets that clear their
orders, and the money they pay with. It imports `sim.world`, `sim.constants` and the walled packages' `api.py` (geography, labour), never `sim.engine`.
The engine reaches it through the markets module's port, `sim/markets/port*.py` (mod effects use `sim/engine/economy_port_effects.py`); the tech tree, the founder, projects
and screens ask the port questions (a price, a wage, a rate, what a concern takes) and post
transactions. The package-wall rule is checked by `tools/check_package_walls.py` (economy, agents, labour, geography and ui; `tools/done_check.sh` fails on it); the rule that the economy never imports the engine is part of it.

Contracts: `sim/economy/types.py` (records) and `sim/economy/protocols.py` (the year order and what
each module offers). Outside code imports only `sim/economy/api.py`, the package's published surface
(`docs/architecture/PACKAGE_WALLS.md`). The port reads the map from the geography module (`map_for_agent_economy`, `sim/markets/port_world_map.py`) and hands the economy its tiles and that map
through the setup.

## Choices and why

**Annual step, clearing within the year.** Inventory-target price rules assume many ticks a year; at
one tick a harvest failure would show as rationing at last year's price and a spike only a year later.
So each market clears within the year at the price where buyers' schedules meet sellers' offers, and
the dynamics come from what carries between years: stocks and the reservation prices their holders
set, output decided on last year's price (a cobweb lag), producers idling and exiting, cash balances,
debts and the money stock.

**Buyers' schedules carry a floor and a budget.** `goods_market.quantity_at(bid, price)` is a floor (what is needed
whatever the price) plus a part that falls with price, capped by what the buyer can pay. With no
seller the price rises until budgets bind, so there is no price ceiling or floor constant: a famine
price is the price at which the poorest cohort's money runs out, and the unmet floor is recorded for
demography to read.

**Sellers' reservations follow their situation.** A producer offers new output at no less than its
variable cost; a holder of stock at what it expects to get next year less carrying cost and spoilage; a
seller short of cash for debts or wages below that; a waste product below zero.

**Wages come from the labour core; the interest rate is sticky.** Every employer's staff are bids in the core: the seats', firms' and
states' staff books are posted as bids by `sim/markets/port_staff.py` (the standing places plus the one-year
orders, such as commissions and herd labour, as one bid per trade: `places_with_once`) and the books are the people the
clearing hired (paid soldiers are the state's staff, posted like any crew; the state's call-up of hours for its works and its conscripts is handed to the economy as hours per worker, `sim/markets/port_levy.py`) (what is left is `Complaints/964`, `556`). The economy keeps its workforce as
the labour core's `MarketState` (people per tile, trade and ability band; `labour_state.py`) and each
year hands the core the producers' bids as tranches of falling value (`labour_bids.py`), the outside
option and routes to bordering tiles (`labour_inputs.py`). Demography's people per tile are the one count: the core's workers
and trainees are rescaled to it each year and the core adds no entrants or leavers of its own (`Economy._follow_population`).
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

**Space is tiles.** A good's market area is the set of tiles between which
carriage costs less than a share of its value, so silver trades across a civilisation and grain within
a tile or a few. The cost of a haul between tiles is geography's route cost (`sim/economy/tile_costs.py`
asks `route_costs`, see `sim/geography/INTERFACE.md`): rivers, coasts, grade and sea lanes come from the
map, and the economy supplies only its money per tonne-km for each mode. Carriage crews bid in the labour core in their mode's own trade (`sim/economy/carriage_hours.py`), and carriage is their pay.

**Stock-flow consistency.** Every movement of money or goods has a counterparty. Money and goods enter
or leave only through named edge accounts (`types.EDGE_*`). Engine postings that do not yet name a
payer or payee are booked against `edge:legacy` (`EDGE_LEGACY` in `types.py`); its volume should fall to zero
(`grep -rn "EDGE_LEGACY" sim --include=*.py` lists the postings; `Complaints/closed/382` is the multi-player plan).

**Money takes each society's own form.** A civilisation's coin standard names its regime: struck coin
(a mint buys metal at parity less its charge and strikes it; the charge is the issuer's seigniorage),
weighed metal (money is the metal by weight, no issuer), or a commodity (cacao beans). The mint holds
a real metal stock, sells only what it holds and strikes only what it buys (`mint.py`), so mined metal
raises the money stock and, with a lag while it sits with savers, prices. The mint is served first among the metal's
buyers (`mint.MINT_PRIORITY`: it pays up to the mint price, above the ask, so other buyers cannot leave it rationed to nothing) and
its yearly capacity counts the wear of the coin it strikes (`yearly_monetisation`).

**The state spends what it raises.** Its revenue buys hours and goods in the same markets as everyone
(`state_budget.py`); a deficit is covered by its policy's order of borrowing, issuing (fiat) or
debasing (struck coin) (`state_finance.py`, `state_policy.py`). Printing to cover a deficit that grows
with prices runs away.

**Households save and lend.** Spending is mean net income plus the yearly share of the account held (cash and money lent)
plus, for shares owned, the same share of share wealth over a target (`households_buffer_stock`, after Eurace's
`Household_determine_consumption_budget`): a household at a steady income does not save out of it. The excess is spent down at a limited pace
(`WEALTH_DRAWDOWN_LIMIT`, set by the larger of this and last year's income), and a year's spending falls by at most
a limited share of expected spending (`SPENDING_CUT_LIMIT`), so a swing in the target does not swing demand for
durables. The cap follows the budget a household placed, not the money a rationed market let it spend
(`durable_stock.update_expected_spending` takes `planned_spending`), and the share wealth the rule reads is the one recorded at the
last close, before the year's wages leave the producers' accounts (`households_buffer_stock.share_wealth_carried`); what they hold
beyond buffer and spending is offered to borrowers. Loans are claims in the lender's wealth
(`credit_claims.py`): a default is the lender's loss and cuts its spending. Producers borrow for plant,
merchants for cargo their cash cannot buy, households for a shortfall with income ahead.

**Sellers raise asks when buyers are turned away.** After the unsold search lowers asks to where everything sells
(`unsold_search.py`), producers whose buyers were turned away raise theirs to the highest common level at which buyers still ask for
the whole stock, no higher than the buyers could pay (`demand_search.raise_asks`, called by `unsold_search.raise_sold_out`). A sold-out
seller's expectation is not pulled toward cost (`ask_adjust.regressive_weight`), and a crowd of price takers asks its expected price for
stock it expects to sell (`seller_offers.expected_ask`). The logit allocation (`goods_market_logit.allocate`) redirects rationed buyers
to sellers still holding stock, round after round, until no stock is reachable. Credit rations by quantity at the lenders' ask and
cuts a request the premium prices out to what its pledge bears (`credit_rate.py`, `credit_cap.py`; open: `Complaints/641`).

**Demand brings makers.** Where buyers wanted more of a good than was sold, beyond what its makers'
idle capacity could have added, a recipe the society knows that pays at the price bid starts or grows
the tile's producer of it (`entry.py`, `entry_year.py`), its owner staking cash and borrowing plant
only up to that stake. A market with buyers and no maker in its area draws a trial newcomer judged at
its own full cost plus a margin, since its remembered price is stale (`entry_trial.py`). A good with no
known recipe gets no maker. The recipes the society knows are not fixed at the opening: each year the port
matches them to the techniques some producer in the society runs (the founder's, any firm's concerns), and a
newly allowed recipe, with a market for any good that had none, is handed to the economy through its api
(`sim/markets/port_late.py`, `sim/economy/late_recipes.py`); the saved opening carries them, so a resumed game
rebuilds the same set. Real output follows the economy's cleared quantity only for goods such a recipe makes
(`Complaints/closed/478`); for every other good it still reads the opening's reference. Every recipe that pays draws a newcomer, best first, each for a share of
what the better ones leave: no cap on newcomers per market a year. Where makers exist and sellers have
raised asks until buyers are no longer turned away, a market whose usual (smoothed) price stays above
its cheapest recipe's entry price for as many years as a loser waits to exit draws newcomers sized to
what the bids take at the entry price, no faster than incumbents change their output
(`entry_margin.py`); an earlier attempt at this destabilised staple prices
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

**Producers pay out and shed.** A producer pays its owners the cash above next year's production spending, commitments, plant to
rebuild and a buffer of its running costs (`firm_finance.cash_to_keep`, `excess_cash`, `payout`). Land rent is a cost of its year
(`year_ledger.note_paid_outside_markets`), and a producer whose remembered earnings after every cost are negative closes that share of its capacity, no
more than a year's change in output (`producer_losses.shed_share`).

**Producers leave.** A producer whose year did not cover its costs and plant charge counts a loss year;
after enough of them, with no variable margin left, it exits: its cash repays its lenders first, the
rest and its goods go to its owner, and what the cash could not repay is the lenders' loss
(`producers_close.py`, `producer_exit.py`). Plantless capacity (mines, most workshops) follows use, so
idle hands are let go instead of flooding back on a price spike; a producer whose capacity has
dwindled to nothing, with no plant coming and no debt, closes (`entry.producers_to_close`).

**Growing is judged at the price growth leaves.** A producer with plant asks a loan to expand only if the new
capacity still earns more than the live rate at the price expected once its own output is on the market, read off
the buyers' schedules of the year's book (`expansion_price.py`); a newcomer drawn by a margin is sized by the gap
at its entry price (`entry_margin.py`), which keeps the price after its additions at or above that price.

**Prices that have not traded are not market prices.** Each market remembers how long ago it cleared;
the price index counts only goods traded recently, and the game shows an untraded good at its cost
of making at live prices, or flags it stale (`notional.py`). A
year's trade moves a remembered price in proportion to its volume against the market's usual volume, so
a sliver of trade at a freak price does not become the price everyone plans from.

**Start.** A hidden spin-up runs the economy from the opening population, land, techniques and the
solver's costs until prices and the interest rate settle, cached on disk per civilisation (keyed on
the data and source).

**Other countries** trade as external sellers and buyers booked against `edge:external`, at the
partners' prices. The year's trade settles in the partners' coin ledgers (`sim/foreign_trade/payments.py`), so a
partner paying out coin sees its prices fall, and it spends at most a share of the coin it holds
(price-specie flow). The types allow partners to become full economies, and later players.

**Trader actors' cargo** is not booked against `edge:external`. Each cargo leg that touches home gets an account in
the book (`sim/markets/port_cargo.py`): a landing cargo arrives over the partner's own edge
(`external_edge(partner)`) and is offered, a taking cargo is bought with funds the trader put in; after the clear the
account's money goes back to the trader's purse over `edge:cargo` and the goods nobody took return over the
partner's edge. The partner's side settles in that partner's coin ledger and the route's carriers
(`sim/foreign_trade/cargo.py`), and the trader's purse is trued up from its decision-time booking to the result.
The trader's purse is an account in the same book (see "Actors' money and debt in the book"); the cargo account is funded
and emptied over `edge:cargo`, and the trader's booked result is trued up to what the book gave.
A landing cargo's sales and a taking cargo's purchases cross the border, so the state's customs assess them: the
economy is told which accounts are such (`EconomyYearInputs.import_accounts`, `export_accounts`), its ledger counts their
sales and purchases as imports and exports, and the customs bases tax the cargo account out of its takings. A cargo
bought for abroad with nothing left in its account owes no export duty (the duty is taken from what the account holds).

**The founder's concerns sell in the same markets**, offered at their output's cost at the economy's
own prices and wages; the unsold goods go back out over `edge:legacy`. A concern whose output the economy trades is paid what the clearing pays
for the units buyers took, gross, less its inputs' cost (`sim/markets/port_seats.py settle_seats`, `sim/production/book_sales.py`);
the engine's revenue estimate covers only the concerns that do not sell in the book.

**Seats', firms', states' and other actors' sales and purchases are book orders.** A seat's buy or sell command waits for the year's clearing as an order (`sim/markets/port_goods_orders.py`); the actors' are handled by `sim/markets/port_actors.py`. A
`market_sale` is noted through the year and, when the economy's year runs, becomes an offer from an account named for the
seller, at what its concerns cost to make the good (a good with no concern behind it at what the market pays). What the
account holds afterwards is the seller's proceeds, turned into its coin over `edge:exchange`; what did not sell goes back
out. A concern whose output sells in the book does not also book the engine's estimate of its takings. A
`market_purchase` becomes a bid for a fixed quantity from an account named for the buyer, whose budget the buyer's coin
turned into the economy's unit; the goods it gets are used up and the unspent budget returns. The state pays the money of
a line's materials this way and the rest of the line as before. The actors' coin and the economy's unit are two
currencies of one book (the actors' accounts live in the economy's book once it opens; each owner saves only its own
currency), meeting at `edge:exchange` at the opening wage that fixes the unit.

## Actors' money and debt in the book (`Complaints/closed/115`)

The engine's actors (firms, the state, traders, interest groups and the strata) keep their money as accounts in a
double-entry book (`sim/book.py`, the class the economy's own agents use; the actors' instance is
`ActorsState.purses`, `sim/agents/purses.py`). The book exists from the first posting of a game and is saved with
the actors. The decision for who may owe what, and to whom:

- A purse is never negative. Only edge accounts (the edges named in `sim/agents/edges.py`) may go below zero.
- A debt is a loan claim. An actor that pays more than its purse holds draws the shortfall on its facility: the pool
  puts the money into its purse and holds one claim for the principal. Money that comes in repays the claim before it is
  kept. `Actor.money` stays the net position (purse less claim), so every reader keeps its meaning; `Actor.debt()` is the
  claim's principal and `spendable` the purse above zero plus the credit still open.
- No money appears from nowhere. The pool's funds are real: the accounts that offered funds at the yearly meeting (a
  state's reserve, a firm's spare cash) and the economy's own lenders (cohorts' savings, banks, funds). When the pool lacks
  what a draw needs, `Purses._fund_pool` takes it from the economy's lenders (`economy_api.lender_listing`, reached through
  the markets view `agent_lender_listing`) cheapest ask first, only lenders asking no more than the draw's rate, each
  lending no more than it offered and its account holds. The money crosses `edge:exchange`: units from the lender to the
  exchange, coin from the exchange to the pool, at the coin per unit. A lender's claim on the pool is a deposit; interest
  is shared among the deposits at the yearly settlement and an economy lender is paid it in units into its own account,
  and gets its deposit back, the same way, from what the pool holds beyond its lending. The only exception is a
  bookkeeping reset (`Purses.set_net`), which stands the account outside the book behind the debt it writes.
- A draw beyond what the borrower may be lent (`Purses.limit`, set by the actors module to the borrower's `rule_limit`,
  the economy's rule alone) or beyond what the lenders can supply is refused (`Borrower.draw_limit` is the rule's limit
  cut to what the pool and the lenders supply, the very gate `Purses.drawable` applies): `Purses._draw` raises `InsufficientFunds`, nothing moves, and the
  ledger turns it into a `cannot_pay` refusal. A cover is all or nothing. The actor does with less (a staff bid, a
  purchase, a line of spending) or logs an `unpaid_charge`. A bond that falls due and cannot be paid stays on the book as
  debt and falls due again.
- The market rate and what an actor may draw are the economy's own: `Borrower.rule_limit` asks the credit market's
  `fundable_amount` (the rule the clearing applies to every request, priced by the economy's risk premium and floored by
  the lowest lender ask), and the rate on a draw is the market rate plus that premium, for the seat's arrears and the
  credit lines alike. Interest the pool receives waits in it until the yearly settlement; `state_lending` is the claims the
  state holds. A lender's own cash book is told of each loan and repayment so its purse still equals its books.

## One money per labour hour (`Complaints/closed/115`)

What an hour of work is worth in the game's coin is one figure: the agent economy's wage for the unskilled trade at the
base tile. It reaches the labour package through `labour_wage_schedule.wage_schedule`, which reads `agent_wage_at` for the
unskilled trade (the markets view of `PriceReads.wage_per_hour_at`). That figure and every other trade's wage come
from one rule (`sim/economy/trade_wages.py`), for the home country and a partner alike: the wage the trade's labour market
paid (the labour core's area wage; the core clears a (trade, area) only where it has workers or bids, so a trade nobody works or hires in an area has none there; a country's figure for a trade is the mean of its areas' wages weighted by hours hired, else by the people working the trade there, else plain); else, only for a trade the memory holds no wage for in any area (before the first clearing, or a trade admitted after it), the opening wage of the trade times `opening_wage_level`; else, for a trade hired or worked somewhere but not in this scope, the unskilled wage of the same scope times one
plus the trade's training premium; and where the scope has no unskilled wage either, the opening unskilled wage times
`opening_wage_level` times one plus the premium (`priced_trade_wage` in `sim/economy/trade_wages.py`; the caller says whether the memory holds a wage for the trade anywhere, `MarketMemory.holds_wage_for`). The opening wage therefore never stands in for a trade the economy has priced elsewhere: it would be frozen at the opening while the area's wages move. A trade id the
setup does not know is an error. Before the economy has opened there is
no wage to read, so the opening is counted at the opening figure (`money_per_labour_hour` times the home price level); the
economy's opening (`open_agent` in `sim/markets/port.py` sends `RepriceOpeningMoney`; `sim/engine/opening_money.py` does the
repricing) then reprices everything counted at that figure, the
founder's and every seat's purse and the tree's money fields, by the ratio of the two, and sets
the markets module's `money_from_economy` flag. From then on living costs, node money, the constants stated in labour hours
(`money_units.PricedInLabourHours`) and hiring all use the economy's wage, so a purse buys the hours it was meant to.
The two figures differ because the solver costs the coin's metal at its labour hours, while the
economy fixes the metal's price in coin and lets goods and wages follow the money stock. The tests are `sim/tests/test_one_money_per_labour_hour.py` and `test_open_agent_reprices_money.py`.

## Domestic trade has one owner

Trade between the places of the home country is the economy's merchants (`sim/economy/merchants.py`): agents in the
book with cash, who buy where a good is cheap and carry it to where it is dear, paying the carriers. Trader actors take
the routes that cross a border (their cargo accounts are in the book). Giving trader actors a second domestic router
would carry the same gap twice, the duplication that `Complaints/closed/405` closed for foreign trade, so there is none.

## Heuristics

Every adjustment speed, cash-balance target and expectation rule is declared with
`sim.constants.declare(kind="temporary_heuristic")` beside its use. `python3 sim/constants.py --kind
temporary_heuristic` lists them.

## Validation

Distributions over civilisations and seeds, never dated events: wage-to-grain ratios in a plausible
band, grain more volatile than metals, harvest shortfalls raising grain prices in the same year, a metal
influx raising the price level with a lag, inflation rising with an issuer's printing, and money
conserved every year.
