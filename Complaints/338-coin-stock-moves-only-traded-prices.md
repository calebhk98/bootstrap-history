# A drained or swollen coin stock moves only traded prices

**Status:** partly - one coin stock now moves every good's price and every wage in the home money, traded or not (`Sim.home_price_level`, applied through `money_per_labour_hour`); velocity and real output are still fixed, the debt rate does not follow the stock, and authored money amounts are not revalued (Complaint 381)

Foreign trade now moves coin metal between economies (`Complaints/323`), and a
stock above or below its opening level scales the prices used to compare the
two markets (`sim/world/balance_of_payments.py`). Domestic prices, wages and
the debt rate do not follow the stock: money is not revalued when its coin
metal floods or runs short (`Complaints/135`). A partner that receives a
great deal of coin therefore lowers only its traded prices, not its own
market, so the correction through prices is weaker than a real economy's.

## Evidence

`python3 sim/foreign_trade_report.py --years 100 --partner <id>` prints the
home coin stock and traded-price level by decade; the market book's price
ratios and the wage schedule do not move with them.

## What it would take

A price level for the whole economy from its coin stock against output (with
velocity and real output as modelled quantities, not the fixed share the
opening stock uses now), read by wages, the debt rate and the market's
long-run costs.

Related: 109, 300, 324, 326, 339, 346, 347, 350, 351, 353.

Owner decision (2026-10-02): should not be possible; it points at the economic model, where one coin stock should move every price.

## Done (Complaint 375)

The price level is the coin stock over the opening's, read by every price and wage in the home money (`sim/engine/foreign_payments.py:home_price_level`, `sim/engine/labour_wages.py:wage_schedule`, `sim/engine/incumbent_prices.py:_material_prices`). The coin metal is held at the mint's standard so trade still pulls coin back (`_coin_metal_price`). `sim/tests/test_per_producer_supply.py` doubles the stock with goods fixed and checks every price, a good that crosses no border, and the wage; a drained stock lowers them. Goods are fixed in the sense that real demand does not move (it is read in labour hours). Still to build: velocity and real output as modelled quantities in place of `MONEY_STOCK_YEARS_OF_WAGES`, the debt rate, and Complaint 381.
