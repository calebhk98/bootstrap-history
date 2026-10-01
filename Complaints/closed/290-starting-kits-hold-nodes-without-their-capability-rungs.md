# Starting kits hold nodes without the capability rungs those nodes name

**Status:** closed - every shipped start now holds the capability rungs its held nodes need

Moving the capability names out of the capital field and into `pre` (283) made 84 nodes in `data/branches/50_textiles_consumer_deep.json` state the rungs they really need. Several starting kits already hold those nodes without the rung, which `python3 sim/simulator.py validate` reports under "held-without-prereq" and "rung-gap" (before and after, per civilisation: England 7 and 1 became 11 and 5; Norse 4 and 0 became 7 and 3; Rome 3 and 1 became 7 and 5; Han and Mexica did not move).

## What it would take

For each civilisation, decide from `docs/knowledge/` whether the people of that date really had the tolerance or heat rung (`cap_tol_100um` for the needles, `cap_heat_1100` for bottles, enamelling and asbestos cloth), then either add the rung to the starting techs with its own prerequisites or drop the held node. Find the gaps with `python3 sim/simulator.py validate` and `python3 sim/civ_start_check.py`.

## Resolution

Rome, England, Norse and Han hold bloomery iron, bronze, glass or cast iron, so they now hold `cap_heat_1100` (and its prerequisite `refractory_fireclay`). The needle nodes (`tx2_needle`, `tx2_eye_pointed_needle`: polished steel needles and the machine-sewing needle, gated on the 0.1 mm rung that needs the three-plate method) are dropped from Rome, England and Norse, who did not make them; no start holds the 0.1 mm rung. `python3 sim/simulator.py validate` prints rung-gap 0 for every civilisation, and `test_no_shipped_civilisation_holds_a_node_whose_capability_rung_it_lacks` in `sim/tests/test_civilisation_start_agrees.py` holds it. The hand needle itself has no node (Complaints/297).
