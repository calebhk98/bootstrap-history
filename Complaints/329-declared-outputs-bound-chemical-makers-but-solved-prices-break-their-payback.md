# Declared yearly outputs derive some makers' revenue wrongly; the rest still need a basis

**Status:** open

Declaring `annual_output_t` with an `annual_output_basis` moved a node from authored to derived revenue (`python3 sim/node_revenue_report.py`). Some declarations were withdrawn because the derivation then gave a wrong answer, and these nodes are listed in `STILL_UNBOUNDED` in `sim/tests/test_node_output_data.py`:

- Makers whose entries add less than their staff cost at solved prices derive zero revenue (caustic soda, glycerol, superphosphate, polyethylene, gunpowder, mirror amalgam). Either the inputs of their entries are priced too high against the product, or the entries understate yield. Mirror amalgam's entry also states no labour hours.
- Makers whose derived payback fell under the floor, because the solved price of the product follows the incumbent labour-heavy route (Solvay soda against Leblanc, bleaching powder, hand papermaking whose revenue is only its wages). This is the cost-priced concern problem of `Complaints/319`.
- Crucible steel and industrial-scale zinc declare output but no production entry exists that they gate, so no entry can be bounded; they need an entry (crucible melt of blister bar; Belgian horizontal retort works) with a stated plant.
- Extraction nodes and lines whose basis unit is not a kilogram (see the test).

Fix: correct the entries or prices, then restore the declarations and delete the node from `STILL_UNBOUNDED`. Do not invent a figure to satisfy the floor. See `Complaints/318`, `319`, `283`.

## Update (concern-margins-and-capital-charge)

The capital charge did not repair the zero-revenue makers: none of caustic soda, glycerol, superphosphate (phosphoric acid), polyethylene, gunpowder or mirror amalgam has a plant in its entry, and their entries state no labour (the data files say "Labour is left out"), so the solved price equals the inputs and a batch adds nothing. They need entries with labour borrowed from a named neighbour and a stated plant, not a figure here. Solvay soda stays withdrawn: its entry adds far more than its staff costs, because the civilisation's price for soda is the labour-heavy route's, so its derived payback falls under the floor (`Complaints/336`).

Restored with a declared output and a basis taken from the entry's own hours: bleaching powder (about three hundred tonnes) and hand papermaking (one vat, about half a tonne). Both earn their staff's wages, since neither entry states a plant.

Related: 140, 295, 317, 335, 337.
