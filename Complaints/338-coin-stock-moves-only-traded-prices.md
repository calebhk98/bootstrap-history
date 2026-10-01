# A drained or swollen coin stock moves only traded prices

**Status:** open

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
