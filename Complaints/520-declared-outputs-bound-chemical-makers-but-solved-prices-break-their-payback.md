# Declared yearly outputs derive some makers' revenue wrongly; the rest still need a basis

**Status:** open

Declaring `annual_output_t` with an `annual_output_basis` moved a node from authored to derived revenue (`python3 sim/node_revenue_report.py`). Some declarations were withdrawn because the derivation then gave a wrong answer, and these nodes are listed in `STILL_UNBOUNDED` in `sim/tests/test_node_output_data.py`:

- Makers whose entries add less than their staff cost at solved prices derive zero revenue (caustic soda, glycerol, superphosphate, polyethylene, gunpowder, mirror amalgam). Either the inputs of their entries are priced too high against the product, or the entries understate yield. Mirror amalgam's entry also states no labour hours.
- Makers whose derived payback fell under the floor, because the solved price of the product follows the incumbent labour-heavy route (Solvay soda against Leblanc, bleaching powder, hand papermaking whose revenue is only its wages). This is the cost-priced concern problem of `Complaints/462`.
- Crucible steel and industrial-scale zinc declare output but no production entry exists that they gate, so no entry can be bounded; they need an entry (crucible melt of blister bar; Belgian horizontal retort works) with a stated plant.
- Extraction nodes and lines whose basis unit is not a kilogram (see the test).

Fix: correct the entries or prices, then restore the declarations and delete the node from `STILL_UNBOUNDED`. Do not invent a figure to satisfy the floor. See `Complaints/461`, `462`, `287`.
