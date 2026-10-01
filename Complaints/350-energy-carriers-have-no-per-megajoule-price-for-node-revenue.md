# Node revenue cannot value energy bought or sold

**Status:** open

`sim/engine/node_output.py` derives a node's revenue from what its production entries make less what they buy. It leaves energy out: `goods` prices `thermal_mj`, `mechanical_mj` and `electrical_mj` at one flat pool figure, while each entry pays the price graded to its own temperature or kind of work (`recipe_cost_and_allocation` in `sim/solve_prices_core.py`), and the flat figure can exceed the entry's own solved output price (compare `cement_portland_kg` with its thermal draw). So energy an entry draws is not deducted (revenue is a little high for heat-hungry entries such as cement and glass), and a line whose product is an energy carrier is skipped.

The power nodes (steam, water, internal combustion, electrical generation and grid) sell energy and are mostly ungated by any production entry; they are the bulk of the nodes still resting on the payback cap (`python3 -c` over `data.load()` listing nodes with `_revenue_basis == "authored"` and `rev_hours < _rev_hours_authored`).

Fix: expose the graded price per entry (or per carrier and requirement) from the solver, deduct it in `node_output.output_baskets`, and give power nodes an output of megajoules a year from their capacity so the cap can go.
