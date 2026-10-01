# Derived node revenue is computed once, at the reference civilisation's techniques

**Status:** open

`data.load()` derives each output node's revenue from solved prices once, held at the reference civilisation's starting technologies, and every civilisation shares it (rebased to its coin). A concern in a civilisation whose iron, fuel or power differ earns the reference civilisation's net. The yearly market ratio moves it by year but not by what that civilisation can make or buy. Also transitional: a node's purchased energy is valued at the pool price, not the temperature or kind of work its entry needs (`sim/engine/node_output.py`), and a good priced at the "mature" fallback enters a concern's revenue at a technique nobody in reach holds.

What it would take: derive the baskets per civilisation (or per held gate set, cached the way the solver caches) and let the solver expose each entry's graded energy price. Measure with the node revenue table for two civilisations. See `Complaints/395`, `Complaints/39`, `Complaints/287`.
