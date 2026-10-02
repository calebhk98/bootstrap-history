# Goods prices follow a solved long-run cost of the techniques in use, not each producer's cost and supply

**Status:** partly - the market now clears producers' offers, each at the cost of the entry that producer runs, against demand, and the society-wide solved cost is no longer the market price; household prices, the founder's own sales and which entry a producer holds still read society-wide figures (list at the end)

The owner's principle: a market price comes from what is in the market, supply against demand. A producer's cost comes from the technique that producer runs. Supply comes from producers who actually produce. The market knows nothing of the tech tree. A technology that is invented but unused changes no price.

## Design note

**Producers.** A producer is anything that puts a good on the market: a founder concern, a firm's concern, a trading partner, and the society's incumbent producers taken as one background producer. Each offers a quantity at a reservation price, the lowest it will sell at, which is its own unit cost from the entry it runs, at the prices it pays for inputs. A producer whose cost is above the clearing price sells nothing that year. A cost can be negative (a joint by-product that costs money to dispose of is sold at any price, never floored at zero; Complaint 309).

**The market.** `sim/world/market.py` with `sim/world/producer_market.py` clears the year's offers against demand: demand is a curve (it falls as the price rises, it does not vanish), supply is the incumbents' output, which rises with price as dearer workings come in, plus every offer whose reservation price the clearing price reaches. One price per good comes out. The market takes tonnes and ratios and imports nothing from the tree; `sim/tests/test_producer_market.py` holds that as a structural test.

**The solver's role.** Computing what one unit costs for one entry at given input prices (`sim/engine/entry_cost.py`, `sim/engine/producer_costs.py`); the incumbents' cost of every good, from the techniques the society started with, at the opening's wage ratios (`sim/engine/incumbent_prices.py`); and a baseline for a good no incumbent makes but some producer runs a technique for (labelled temporary there). It no longer sets a price for the whole society from the cheapest entry any producer runs.

**Money.** Coin is one stock. The price level of every good and wage in home money follows the coin stock against the opening's (`home_price_level` in `sim/engine/foreign_payments.py`, applied through `money_per_labour_hour`), traded or not. The coin metal itself is held at the mint's standard (`_coin_metal_price`), so a flood of coin makes imports cheaper and drains it back through trade (Complaint 338). Within the year-close every commodity clears at the level the year opened with; the coin that year's trade moves counts from the next year.

## What changed

- `Sim._material_prices` is the incumbents' cost in this coin; the price the market posts is that times `market_price_ratio`, which now comes from the clearing of offers.
- Every seller records the cost of what it sells (`GoodsMarket.note_sale(..., reservation_ratio)`); firms sell each concern at its own entry's cost; the founder's running output concerns offer too (`ProducerCostsMixin.founder_concern_offers`).
- A technique held, or run by one producer, does not reprice the incumbents or any other producer.

Tests: `sim/tests/test_producer_market.py`, `sim/tests/test_per_producer_supply.py`. Measure a change against its base with `python3 sim/market_trace.py rome_100ad` (and `han_china_100ad`): posted prices, price level, output per head, capital, firm count and CPU by period; `python3 sim/perf_fingerprint.py check --quick <recorded file>` shows where a run first leaves the base.

## Still open

- Household prices (`GoodsMarket.household_prices`) and so household real income read the incumbents' cost, not the posted price; an entrant's cheaper good shows in the quantity the market clears, not yet in what a wage buys.
- A concern holds the entries of its own node and of any node some producer runs that makes the same products (`sim/engine/concern_volume.py`, labelled): copying inside a line of business is instant. A producer-by-producer technique set would replace it.
- Founder concerns offer, but the founder's own sales and purchases keep the marginal curves of `material_price_factor`.
- Producers do not choose: see Complaint 376 (profit-maximising offers, idling or exiting below cost).
- `sim/engine/node_revenue.py` and `sim/engine/data.py` still derive revenue and upkeep once at the starting techniques; authored money is not revalued by the price level (Complaint 377).
- Foreign partners offer through the trade module, priced at their own cost; they are not yet a producer in the same list.

Related: 369, 370, 354, 338, 135, 102, 372, 376, 377.
