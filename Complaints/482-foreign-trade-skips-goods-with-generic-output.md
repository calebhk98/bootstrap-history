# Foreign trade skips goods whose output is only a generic estimate

**Status:** open - not started and not contained: it needs sourced output per region and an industrial demand model; with merchants' costs (591) partners are on by default and trade only sourced goods plus goods this society cannot make

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

`python3 sim/foreign_trade_report.py` trades only commodities with sourced
output (minerals, wool, cloth, cotton) plus goods this society cannot make.

## What it would take

Sourced output per region for more goods, an industrial demand model for
intermediates (`Complaints/106`), and a land and labour cap on a partner's
output through its own trades.
