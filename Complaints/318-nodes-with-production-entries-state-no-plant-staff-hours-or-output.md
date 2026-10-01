# Nodes with production entries state no plant, staff hours or output to bound them

**Status:** partly

`sim/engine/node_output.py` bounds a node's yearly output by the plant its entries state (`annual_output_at_basis` on `capital`), by the hours its staff (`sch` + `art`) supply over the entries' `labour_hours`, and by a declared `annual_output_t`. A gated node with none of the three has no output to derive and stays on its authored revenue under the payback floor. Measure: `python3 -c` over `data.load()` and `node_output.entries_gated_by` listing nodes with `_revenue_basis == "authored"` whose id gates entries. They are mostly chemical and process nodes (the `chm_*` family, gunpowder, hand papermaking, the rope walk, vegetable tanning, electrolysis, mirror amalgam, uranium and plutonium plants): the entries state the batch but nobody says how many batches a plant of that kind runs in a year.

Separately, several nodes declare `annual_output_t` (crucible steel, clear glass, the high-temperature furnace, lead metallurgy, industrial-scale zinc) yet gate no production entry, so the declared tonnes name no product: the declaration feeds nothing, and the entries that make the material gate a different node. List with `python3 -c` over `data.load()` for nodes with `annual_output_t` and no `entries_gated_by`.

Extraction and by-product entries (`extracted_from` with no capital or inputs: peat, opium, flotation concentrates, air gases, coal seams) are skipped on purpose: a deposit or a parent stream sets their output, not staff.

Fix: state a plant (`capital` with `annual_output_at_basis`, a physical fact with a stated basis) or a declared tonnage for each, or re-point the declared ones to the node that gates their entries. Do not invent a figure to make the payback floor go away; each needs a source for the plant's yearly throughput. See `Complaints/283`.

Related: 140, 295, 317, 329, 335, 336, 337.
