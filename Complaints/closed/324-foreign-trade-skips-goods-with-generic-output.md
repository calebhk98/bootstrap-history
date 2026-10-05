# Foreign trade skips goods whose output is only a generic estimate

**Status:** closed - folded into 407

`_output_is_sourced` in `sim/engine/foreign_economies.py` (labelled a temporary
heuristic) lets a good this society makes cross a border only when
`resources.json` or `commodities.json` gives its output; the book's reference
for any other good is a price-derived estimate, often the ceiling, and trading
against it moved implausible tonnages. A partner's households' demand also
leaves out goods bought only as inputs to other goods, because the household
model's absolute levels for them are not credible (see the
`sim/engine/market_demand.py` docstring). A partner's land, labour and trades
do not cap its output either: a made good opens with capacity equal to its
households' demand (`FOREIGN_OPENING_IN_BALANCE`).

## Evidence

`python3 sim/foreign_trade_report.py` (script since removed; recover with `git show 97473f1:sim/foreign_trade_report.py`) trades only commodities with sourced
output (minerals, wool, cloth, cotton) plus goods this society cannot make.

## What it would take

Sourced output per region for more goods, an industrial demand model for
intermediates (`Complaints/102`), and a land and labour cap on a partner's
output through its own trades.

Related: 109, 300, 338, 346, 347, 350, 351, 353.
