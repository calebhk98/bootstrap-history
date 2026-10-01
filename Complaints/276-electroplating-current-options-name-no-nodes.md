# Electroplating's source-of-current options name ids that are not in the tree

**Status:** partly - misspelt node ids fixed and rejected by validate; `validate` also counts commodity-style options that are the tail of one node id; the per-id content decisions remain

The electroplating node lists `dynamo_shunt_wound` and `rectifier_metal_layer` among its options for a source of current. Neither id exists in the tree; the real nodes are `el2_dynamo_shunt_wound` and `el2_rectifier_metal_layer`. So that option group has fewer real choices than it appears to have, and if `power_grid` is not among them it may have none.

What it would take: point the options at the real ids, and add a `validate` check that every option id in a node's alternative groups names a node that exists, so this class of typo fails loudly.

    grep -rn "\"dynamo_shunt_wound\"\|\"rectifier_metal_layer\"" data/branches

Found while fixing complaint 121 (electropolishing), whose own options had the same shape.

## Done

`validate` now errors on an option id in a `req_any` group that is not a node
but becomes one with the owning node's own id prefix (`dynamo_shunt_wound` in an
`el2_` node, for `el2_dynamo_shunt_wound`). The ids it found in the branch
files, electroplating's included, now name the real nodes
(`python3 sim/simulator.py validate`).

## What remains

"Every option id names a node" is too strict as written: the engine
deliberately treats an option that is neither a node nor a material as a
purchasable commodity at a discount (`_substitution_group_best` in
`sim/engine/projects_starting.py`), and many options are written that way on
purpose (`air`, `oil_bath`, `peroxide`). `validate` prints one warning with the
count of such ids. What is left is a content decision per id: make it a node, a
production good, or leave it a commodity. `validate` now also reports how many of those
ids are the tail of exactly one node id (a possible misspelling under another
prefix); the one real typo found that way, `telephone_exchange` in
`el2_load_dispatch_and_scheduling`, now names `if_telephone_exchange`. The
remaining ones listed (`oil_bath`, `peroxide`, `acetone`) are deliberate
commodities or need the per-id decision.
