# A concern's takings do not yet follow the production entries it uses or the drift of its goods' prices

**Status:** closed - a concern's volume and takings follow the techniques the society holds (`sim/engine/concern_volume.py`, `techniques_in_use.py`, `technique_spread.py`; pinned by `sim/tests/test_concern_volume.py` and `test_technique_spread.py`). A node earns only from the output of the entries that name it in `operated_by`; no revenue is authored (`python3 sim/simulator.py validate` prints the census with no authored line), a node that makes no good earns nothing from output and acts through its mechanics. A technique one producer runs reaches other concerns after the copying time (`agents/imitation.copy_years`). `real_output` reads the granted set and the market, the diffusion indices read the seats' builds and the founder's operating ventures, and node revenue reads `society_holdings`.

What was missing (all done):
- Nodes whose revenue is authored (the `authored` line of `simulator.py validate`) have no entries to follow. A node that makes a good should name its entries (`operated_by` on the production entry; do not invent yields, 4.5); a node that makes no good (a science, an institution, a service) should earn through what its mechanics change.
- A founder only ahead of the society (a technique the society lacks) earns more; one the society already holds earns the competitive return. The actors' side already works this way (`agents/imitation.py`: an actor knows what it has copied plus the opening's techniques; the founder's inventions are only `demonstrated`). The node-revenue derivation (`node_rederive.py`) used the founder's `done` as the society's held set; it now reads `society_holdings`. `techniques_in_use` is the set producers run; a concern reaches another producer's technique only after `copy_years` from the year it was first seen running (`technique_spread.py`, the record is `economy.technique_first_run`); the opening's techniques are held from the start. `real_output` and the diffusion indices no longer read `projects.done`.

What was built:
- A concern's line of product is the set of outputs its entries make. It runs the best entry for each line among the node's own and any entry gated by a node some producer runs (`concern_volume.entries_held_for`), at the node's own staff and plant, so an entry whose labour per unit halves lets the same staff turn out more once a producer runs it (`concern_volume_ratio`). Actors' market supply (`SimWorld.concern_output_tonnes`) carries the same ratio.
- Its takings are the loaded figure carried by `concern_value_ratio` (net sales at the solved prices of the techniques in use over the opening's), times the market's spot-over-solved ratio on the baskets it makes now (`node_output_market_factor`): volume times the price the goods market clears at, less what it buys at that price. A technique that cheapens its good lowers its takings unless volume rises with it; a concern on a technique the market has overtaken goes to nothing.
- A technology held but run by no producer changes no price (`Sim.techniques_in_use`, Complaint 375 for what remains).

Measured (a scratch driver, no committed command; seed 1, 150 years from the opening): output-derived concerns are few, and the founder runs few of them; Rome's real output per head moves by under one percent from adoption in the years before the mortality shock, Han's is unchanged. See 354.

Related: 101, 112, 119, 140, 283, 354, 370, 375.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 370 (`closed/370-real-output-ignores-goods-offered-after-the-opening-and-household-income-does-not-follow-wages.md`): real output ignores goods offered after the opening; household income does not follow wages.
- 354 (`closed/354-the-founders-takeoff-needs-costs-that-lag-the-economy-index.md`): the founder's takeoff economy index is gone; the remaining ask is aggregate labour demand cleared against the working population.

Owner decision (2026-10-09): authored node revenue means the economy is still partly fake; this is the next priority after 119 and 135.
