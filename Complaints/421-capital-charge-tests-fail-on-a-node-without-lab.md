# Capital-charge tests fail on a node without `lab`

**Status:** open

`python3 -m sim.tests --only capital_charge`: three checks error with `KeyError: 'lab'`. The tests are "a
concern priced at its solved cost earns wages plus a return on its plant", "the surplus repays what the
plant wears and then some" and "with no return charged a concern earns less than with it".

The path is `sim/engine/node_revenue.py` `apply_revenue` → `_held_under_floor` → `_build_cost_hours`.
It reads `node["lab"]` from the test's hand-built node, which no longer carries it. It fails the same way
on main (`bcd8b65`).

What it would take: decide whether `lab` is required on every node. If it is, the test's node gains it.
If not, `_build_cost_hours` reads it with a default.
