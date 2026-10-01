# Electroplating's source-of-current options name ids that are not in the tree

**Status:** open

The electroplating node lists `dynamo_shunt_wound` and `rectifier_metal_layer` among its options for a source of current. Neither id exists in the tree; the real nodes are `el2_dynamo_shunt_wound` and `el2_rectifier_metal_layer`. So that option group has fewer real choices than it appears to have, and if `power_grid` is not among them it may have none.

What it would take: point the options at the real ids, and add a `validate` check that every option id in a node's alternative groups names a node that exists, so this class of typo fails loudly.

    grep -rn "\"dynamo_shunt_wound\"\|\"rectifier_metal_layer\"" data/branches

Found while fixing complaint 125 (electropolishing), whose own options had the same shape.
