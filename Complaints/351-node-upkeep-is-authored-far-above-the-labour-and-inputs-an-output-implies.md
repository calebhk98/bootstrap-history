# Node upkeep is authored and disagrees with output-derived revenue

**Status:** open

Output-derived revenue (`sim/engine/node_revenue.py`) is what a node sells less the materials it buys, at solved prices. Solved prices are cost-based, so that margin is the labour, capital and risk the price repays, and it sits well under the authored `up_hours` for most of the nodes concerned (measure: over `data.load()`, nodes with `_revenue_basis == "output"` and `rev_hours < up_hours`). A blast furnace's staff-and-plant-limited output nets a small fraction of its authored upkeep. Either upkeep is too high (it should be the staff's wages and the maintenance of the plant, derived from the entries' labour and capital) or the founder is meant to earn a margin over cost that the market layer has to supply (`Sim.market_price_ratio` above one). Derive `up` from the same entries; until then those concerns lose money on paper and the closure rules will treat them as unprofitable.
