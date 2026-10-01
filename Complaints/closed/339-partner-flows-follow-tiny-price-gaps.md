# Partner flows follow tiny price gaps, so a partner ships most of a good it makes

**Status:** closed - merchants have a cost over freight (margin, expected cargo loss on the sea legs, interest at the market rate on the voyage and a wait in inventory) and a response (a share of the way from last year's flow to the arbitrage volume each year, limited by fleet lift and by merchants' capital, `sim/world/trader_response.py`, `sim/engine/foreign_traders.py`); a gap under the cost moves nothing, a sustained shortage draws a small share of the partner's capacity over years; partners are on by default; measure with `python3 sim/foreign_trade_report.py --years 100 --partner <civilisation id>`; what remains is filed as 630

The partner's book opens with capacity equal to its households' demand, and a
good both sides make at nearly the same cost crosses until the gap equals the
freight, however many tonnes that takes. Freight is a small share of the price
of a bulk textile, so the tonnage is set by the fleet and the partner's whole
output, not by any difference in what each side wants. The partner's demand
for goods it cannot make is also uncredible (the household model's demand for
gold is thousands of tonnes, `Complaints/325`), so exports of high-value goods
exceed the exporter's own output in the first decades.

## Evidence

`python3 sim/foreign_trade_report.py --years 100 --partner <han civilisation id>` for the default
civilisation: imports of cloth grow to a large share of the partner's whole
cloth capacity while the route's price gap is a few per cent of the price, and
gold leaves in tonnes above the home output for the first decades. With the
partner as the home economy and the default civilisation as the partner, flows
stay a small share of output and the coin stock stays within a few per cent of
its opening level.

## What it would take

Sourced output for the goods traded (`Complaints/324`), a partner supply
response that reserves its own households' demand before exporting, goods that
differ by origin (so a price gap does not move the whole market), and the
household gold demand fixed (`Complaints/325`). Until then
`enabled` stays false in `data/world/foreign_economies.json`.
