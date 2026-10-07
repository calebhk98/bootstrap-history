# A concern's takings do not yet follow the production entries it uses or the drift of its goods' prices

**Status:** partly - a concern's volume and takings now follow the techniques some producer runs (`sim/engine/concern_volume.py`, `techniques_in_use.py`; pinned by `sim/tests/test_concern_volume.py`). Remaining: most nodes still have authored revenue (Complaint 283), a founder ahead of the society earns no lead, and prices still come from a solved long-run cost rather than per-producer supply (Complaint 375).

What is missing, in order:
- Nodes whose revenue is authored (all but 32 of the tree) have no entries to follow: they need a stated product (Complaint 283).
- A founder only ahead of the society (a technique the society lacks) earns more; one the society already holds earns the competitive return. Today every technique the founder completes is held by the society at once (`done`), so there is no lead to earn.

What was built:
- A concern's line of product is the set of outputs its entries make. It runs the best entry for each line among the node's own and any entry gated by a node some producer runs (`concern_volume.entries_held_for`), at the node's own staff and plant, so an entry whose labour per unit halves lets the same staff turn out more once a producer runs it (`concern_volume_ratio`). Actors' market supply (`SimWorld.concern_output_tonnes`) carries the same ratio.
- Its takings are the loaded figure carried by `concern_value_ratio` (net sales at the solved prices of the techniques in use over the opening's), times the market's spot-over-solved ratio on the baskets it makes now (`node_output_market_factor`): volume times the price the goods market clears at, less what it buys at that price. A technique that cheapens its good lowers its takings unless volume rises with it; a concern on a technique the market has overtaken goes to nothing.
- A technology held but run by no producer changes no price (`Sim.techniques_in_use`, Complaint 375 for what remains).

Measured (`_fp/measure.py`-style driver, seed 1, 150 years from the opening): output-derived concerns are few, and the founder runs few of them; Rome's real output per head moves by under one percent from adoption in the years before the mortality shock, Han's is unchanged. See 354.

Related: 101, 112, 354, 370, 375.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 370 (`closed/370-real-output-ignores-goods-offered-after-the-opening-and-household-income-does-not-follow-wages.md`): real output ignores goods offered after the opening; household income does not follow wages.
- 354 (`closed/354-the-founders-takeoff-needs-costs-that-lag-the-economy-index.md`): the founder's takeoff economy index is gone; the remaining ask is aggregate labour demand cleared against the working population.
